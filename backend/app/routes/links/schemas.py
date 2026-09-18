from typing import Optional

from pydantic import BaseModel, HttpUrl, Field, field_validator

RESERVED_ALIASES = {"shorten", "stats", "analytics", "auth", "static", "my-links"}


class ShortenRequest(BaseModel):
    url: HttpUrl
    alias: Optional[str] = Field(default=None, min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
    expires_in_minutes: Optional[int] = Field(default=None, gt=0)

    @field_validator("alias")
    @classmethod
    def alias_not_reserved(cls, value):
        if value and value.lower() in RESERVED_ALIASES:
            raise ValueError(f"'{value}' is a reserved word and cannot be used as an alias")
        return value
