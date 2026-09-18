from datetime import datetime, timedelta, timezone

from psycopg2 import errors
from psycopg2.extras import RealDictCursor

from app.core.config import BASE_URL
from app.database.db import database
from app.routes.links.schemas import ShortenRequest
from app.utils.click_tracker import discard_pending_clicks, get_pending_clicks, record_click
from app.utils.errors import AppError
from app.utils.link_cache import (
    NOT_FOUND_SENTINEL,
    cache_not_found,
    cache_url,
    get_cached_url,
    invalidate_link_cache,
)
from app.utils.shortcode import generate_short_code

MAX_CODE_ATTEMPTS = 5


def create_short_link(data: ShortenRequest, owner_id: int) -> dict:
    expires_at = None
    if data.expires_in_minutes:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=data.expires_in_minutes)

    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            if data.alias:
                try:
                    cursor.execute(
                        """
                        INSERT INTO links (owner_id, original_url, short_code, expires_at)
                        VALUES (%s, %s, %s, %s)
                        RETURNING short_code, created_at
                        """,
                        (owner_id, str(data.url), data.alias, expires_at),
                    )
                    link = cursor.fetchone()
                except errors.UniqueViolation:
                    connection.rollback()
                    raise AppError("Alias already taken", 409)
            else:
                link = None

                for _ in range(MAX_CODE_ATTEMPTS):
                    cursor.execute("SELECT nextval(pg_get_serial_sequence('links', 'id'))")
                    link_id = cursor.fetchone()["nextval"]
                    code = generate_short_code(str(data.url), link_id)

                    try:
                        cursor.execute(
                            """
                            INSERT INTO links (id, owner_id, original_url, short_code, expires_at)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING short_code, created_at
                            """,
                            (link_id, owner_id, str(data.url), code, expires_at),
                        )
                        link = cursor.fetchone()
                        break
                    except errors.UniqueViolation:
                        connection.rollback()

                if link is None:
                    raise AppError("Could not generate a unique short code, please try again", 500)

    invalidate_link_cache(link["short_code"])

    return {
        "short_code": link["short_code"],
        "short_url": f"{BASE_URL}/{link['short_code']}",
        "created_at": link["created_at"].isoformat(),
    }


def resolve_link(code: str) -> str:
    cached = get_cached_url(code)

    if cached == NOT_FOUND_SENTINEL:
        raise AppError("Short code not found", 404)

    if cached is not None:
        record_click(code)
        return cached

    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT original_url, expires_at FROM links WHERE short_code = %s",
                (code,),
            )
            link = cursor.fetchone()

    if not link:
        cache_not_found(code)
        raise AppError("Short code not found", 404)

    if link["expires_at"] and link["expires_at"] < datetime.now(timezone.utc):
        raise AppError("This link has expired", 410)

    cache_url(code, link["original_url"], link["expires_at"])
    record_click(code)

    return link["original_url"]


def get_link_stats(code: str) -> dict:
    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT original_url, click_count, created_at FROM links WHERE short_code = %s",
                (code,),
            )
            link = cursor.fetchone()

    if not link:
        raise AppError("Short code not found", 404)

    return {
        "original_url": link["original_url"],
        "click_count": link["click_count"] + get_pending_clicks(code),
        "created_at": link["created_at"].isoformat(),
    }


def delete_link(code: str, owner_id: int) -> None:
    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT owner_id FROM links WHERE short_code = %s", (code,))
            link = cursor.fetchone()

            if not link:
                raise AppError("Short code not found", 404)

            if link["owner_id"] != owner_id:
                raise AppError("You do not own this link", 403)

            cursor.execute("DELETE FROM links WHERE short_code = %s", (code,))

    invalidate_link_cache(code)
    discard_pending_clicks(code)


def get_top_links(count: int = 5) -> list[dict]:
    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT short_code, click_count FROM links ORDER BY click_count DESC LIMIT %s",
                (count,),
            )
            rows = cursor.fetchall()

    return [dict(row) for row in rows]
