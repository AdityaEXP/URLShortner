from flask import request

from app.database.redis import redis_client
from app.utils.errors import AppError

WINDOW_SECONDS = 60


def enforce_rate_limit(endpoint: str, limit: int) -> None:
    ip = request.remote_addr
    key = f"rate_limit:{endpoint}:{ip}"

    redis_client.set(key, 0, ex=WINDOW_SECONDS, nx=True)
    count = redis_client.incr(key)

    if count > limit:
        raise AppError("Too many requests, please slow down", 429)
