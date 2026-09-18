from psycopg2.extras import RealDictCursor

from app.database.db import database
from app.routes.auth.schemas import SignupRequest, LoginRequest
from app.utils.errors import AppError
from app.utils.security import (
    create_access_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)


def signup_user(data: SignupRequest) -> dict:
    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE email = %s OR username = %s",
                (data.email, data.username),
            )
            existing = cursor.fetchone()

            if existing:
                raise AppError("User already exists", 409)

            password_hash = hash_password(data.password)

            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (data.username, data.email, password_hash),
            )
            user = cursor.fetchone()

    token = create_access_token({"sub": str(user["id"])})

    return {"access_token": token, "token_type": "bearer"}


def generate_user_api_key(user_id: int) -> dict:
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    with database.get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET api_key_hash = %s WHERE id = %s",
                (key_hash, user_id),
            )

    return {"api_key": api_key}


def login_user(data: LoginRequest) -> dict:
    with database.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE email = %s",
                (data.email,),
            )
            user = cursor.fetchone()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise AppError("Invalid credentials", 401)

    token = create_access_token({"sub": str(user["id"])})

    return {"access_token": token, "token_type": "bearer"}
