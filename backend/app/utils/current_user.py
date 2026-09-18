from flask import request
import jwt
from psycopg2.extras import RealDictCursor

from app.database.db import database
from app.utils.security import decode_access_token, hash_api_key
from app.utils.errors import AppError


def get_current_user_id() -> int:
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise AppError("Missing or invalid Authorization header", 401)

    token = auth_header[len("Bearer "):]

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise AppError("Invalid or expired token", 401)

    return int(payload["sub"])


def get_user_id_from_api_key() -> int:
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise AppError("Missing X-API-Key header", 401)

    key_hash = hash_api_key(api_key)

    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE api_key_hash = %s", (key_hash,))
            user = cursor.fetchone()

    if not user:
        raise AppError("Invalid API key", 401)

    return user["id"]


def get_authenticated_user_id() -> int:
    if request.headers.get("Authorization", "").startswith("Bearer "):
        return get_current_user_id()

    if request.headers.get("X-API-Key"):
        return get_user_id_from_api_key()

    raise AppError("Missing Authorization or X-API-Key header", 401)
