import time
from threading import Lock
from uuid import uuid4

from api.database import SessionLocal, create_all_tables
from api.db_models import RateLimitRequestModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding window rate limiter for /api/predict only."""

    def __init__(self, app, max_requests: int, window_seconds: int):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.instance_id = uuid4().hex
        self._lock = Lock()
        create_all_tables()

    async def dispatch(self, request: Request, call_next):
        if request.url.path != "/api/predict" or request.method != "POST":
            return await call_next(request)

        client_ip = request.client.host if request.client is not None else "unknown"
        now = time.time()
        client_key = f"{self.instance_id}:{client_ip}:{request.url.path}"

        with self._lock:
            window_start = now - self.window_seconds
            with SessionLocal() as session:
                session.query(RateLimitRequestModel).filter(
                    RateLimitRequestModel.client_key == client_key,
                    RateLimitRequestModel.path == request.url.path,
                    RateLimitRequestModel.requested_at <= window_start,
                ).delete(synchronize_session=False)
                session.commit()

                recent_requests = (
                    session.query(RateLimitRequestModel)
                    .filter(
                        RateLimitRequestModel.client_key == client_key,
                        RateLimitRequestModel.path == request.url.path,
                    )
                    .order_by(RateLimitRequestModel.requested_at)
                    .all()
                )

                if len(recent_requests) >= self.max_requests:
                    oldest = recent_requests[0].requested_at
                    retry_after = int(oldest + self.window_seconds - now) + 1
                    return JSONResponse(
                        status_code=429,
                        content={
                            "status": "error",
                            "error_code": "RATE_LIMITED",
                            "message": "Rate limit exceeded. Try again later.",
                        },
                        headers={"Retry-After": str(retry_after)},
                    )

                session.add(RateLimitRequestModel(client_key=client_key, path=request.url.path, requested_at=now))
                session.commit()

        return await call_next(request)
