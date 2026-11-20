"""Модели запросов и ответов API."""
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from .codes import RESERVED

MAX_URL_LENGTH = 2048


class LinkCreate(BaseModel):
    url: AnyHttpUrl = Field(description="Исходная ссылка (http или https)")
    alias: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9_-]{3,32}$",
        description="Своё короткое имя (необязательно): 3–32 символа, латиница, цифры, - и _",
    )

    @field_validator("url")
    @classmethod
    def url_not_too_long(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        if len(str(v)) > MAX_URL_LENGTH:
            raise ValueError(f"Ссылка длиннее {MAX_URL_LENGTH} символов")
        return v

    @field_validator("alias")
    @classmethod
    def alias_not_reserved(cls, v: str | None) -> str | None:
        if v is not None and v.lower() in RESERVED:
            raise ValueError("Это имя зарезервировано сервисом")
        return v


class LinkOut(BaseModel):
    code: str
    short_url: str
    target_url: str
    clicks: int
    created_at: datetime
    last_click_at: datetime | None
