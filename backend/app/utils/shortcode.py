import hashlib

from app.core.config import SHORT_CODE_LENGTH

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _to_base62(num: int) -> str:
    digits = []
    while num:
        num, remainder = divmod(num, 62)
        digits.append(BASE62_ALPHABET[remainder])
    return "".join(reversed(digits))


def generate_short_code(url: str, link_id: int) -> str:
    digest = hashlib.sha256(f"{url}{link_id}".encode()).digest()
    code = _to_base62(int.from_bytes(digest, "big"))
    return code[:SHORT_CODE_LENGTH]
