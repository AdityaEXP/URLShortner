from datetime import datetime, timezone
from typing import Optional

from app.core.config import LINK_CACHE_TTL_SECONDS, NEGATIVE_CACHE_TTL_SECONDS
from app.database.redis import redis_client

NOT_FOUND_SENTINEL = "__NOT_FOUND__"


def link_key(code: str) -> str:
    return f"link:{code}"


def get_cached_url(code: str) -> Optional[str]:
    value = redis_client.get(link_key(code))

    if value is None:
        return None

    if value == NOT_FOUND_SENTINEL:
        return NOT_FOUND_SENTINEL

    return value


def cache_url(code: str, url: str, expires_at: Optional[datetime]) -> None:
    ttl = LINK_CACHE_TTL_SECONDS

    if expires_at:
        seconds_to_expiry = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if seconds_to_expiry < 1:
            return
        ttl = min(ttl, seconds_to_expiry)

    redis_client.set(link_key(code), url, ex=ttl)


def cache_not_found(code: str) -> None:
    redis_client.set(link_key(code), NOT_FOUND_SENTINEL, ex=NEGATIVE_CACHE_TTL_SECONDS)


def invalidate_link_cache(code: str) -> None:
    redis_client.delete(link_key(code))
