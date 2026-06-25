"""Rate-limit persistence cleanup tests."""

from api.database import SessionLocal, create_all_tables
from api.db_models import RateLimitRequestModel
from api.rate_limiter import cleanup_rate_limit_requests


def setup_function():
    create_all_tables()
    with SessionLocal() as session:
        session.query(RateLimitRequestModel).delete()
        session.commit()


def test_rate_limit_cleanup_removes_rows_older_than_ttl():
    with SessionLocal() as session:
        session.add_all([
            RateLimitRequestModel(client_key="old-a", path="/api/predict", requested_at=10.0),
            RateLimitRequestModel(client_key="old-b", path="/api/predict", requested_at=20.0),
            RateLimitRequestModel(client_key="new", path="/api/predict", requested_at=95.0),
        ])
        session.commit()

    removed = cleanup_rate_limit_requests(now=100.0, ttl_seconds=60.0)

    assert removed == 2
    with SessionLocal() as session:
        keys = [row.client_key for row in session.query(RateLimitRequestModel).order_by(RateLimitRequestModel.client_key).all()]
    assert keys == ["new"]
