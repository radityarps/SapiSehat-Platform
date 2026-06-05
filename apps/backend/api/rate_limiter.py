import time
from collections import defaultdict
from threading import Lock
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding window rate limiter for /api/predict only."""

    def __init__(self, app, max_requests: int, window_seconds: int):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next):
        if request.url.path != "/api/predict" or request.method != "POST":
            return await call_next(request)

        client_ip = request.client.host
        now = time.time()

        with self._lock:
            # Prune expired timestamps
            window_start = now - self.window_seconds
            self._requests[client_ip] = [
                t for t in self._requests[client_ip] if t > window_start
            ]

            if len(self._requests[client_ip]) >= self.max_requests:
                oldest = self._requests[client_ip][0]
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

            self._requests[client_ip].append(now)

        return await call_next(request)
