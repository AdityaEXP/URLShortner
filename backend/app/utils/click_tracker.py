from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import CLICK_FLUSH_INTERVAL_SECONDS
from app.database.db import database
from app.database.redis import redis_client

def _clicks_key(code: str) -> str:
    return f"clicks:{code}"


def record_click(code: str) -> None:
    redis_client.incr(_clicks_key(code))


def get_pending_clicks(code: str) -> int:
    return int(redis_client.get(_clicks_key(code)) or 0)


def discard_pending_clicks(code: str) -> None:
    redis_client.delete(_clicks_key(code))


def flush_click_counts() -> None:
    for key in redis_client.keys("clicks:*"):
        pending = redis_client.getdel(key)

        if not pending or int(pending) == 0:
            continue

        code = key.removeprefix("clicks:")

        with database.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE links SET click_count = click_count + %s WHERE short_code = %s",
                    (int(pending), code),
                )


def _flush_job() -> None:
    try:
        flush_click_counts()
    except Exception as e:
        print(f"Click flush failed: {e}")


def start_flush_loop() -> None:
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(_flush_job, "interval", seconds=CLICK_FLUSH_INTERVAL_SECONDS)
    scheduler.start()
