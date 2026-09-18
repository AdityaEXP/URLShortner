import time
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

from app.database.sql import ALL_QUERY
from app.core.config import DATABASE_URL


class Postgres:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    def connect(self):
        for _ in range(10):
            try:
                self.pool = psycopg2.pool.ThreadedConnectionPool(
                    5, 20, dsn=self.database_url
                )

                print("Database connected")

                return

            except Exception as e:
                print(f"Database connection failed: {e}")
                print("Retrying in 2 seconds...")

                time.sleep(2)

        raise Exception("Could not connect to database")

    def disconnect(self):
        if self.pool:
            self.pool.closeall()

    def init_db(self):
        connection = self.pool.getconn()

        try:
            with connection.cursor() as cursor:
                for query in ALL_QUERY:
                    cursor.execute(query)

            connection.commit()
        finally:
            self.pool.putconn(connection)

    @contextmanager
    def get_connection(self):
        connection = self.pool.getconn()

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            self.pool.putconn(connection)


database = Postgres(DATABASE_URL)
