from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
SHORT_CODE_LENGTH = int(os.getenv("TAKE_N", "7"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SHORTEN_RATE_LIMIT_PER_MINUTE = int(os.getenv("SHORTEN_RATE_LIMIT_PER_MINUTE", "10"))

LINK_CACHE_TTL_SECONDS = int(os.getenv("LINK_CACHE_TTL_SECONDS", "300"))
NEGATIVE_CACHE_TTL_SECONDS = int(os.getenv("NEGATIVE_CACHE_TTL_SECONDS", "30"))
CLICK_FLUSH_INTERVAL_SECONDS = int(os.getenv("CLICK_FLUSH_INTERVAL_SECONDS", "5"))
