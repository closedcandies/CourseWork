"""Настройки приложения из переменных окружения."""
import os
from urllib.parse import urlparse


class Settings:
    def __init__(self) -> None:
        self.database_url = os.environ.get(
            "DATABASE_URL", "postgresql://shortener:shortener@db:5432/shortener"
        )
        # Публичный адрес сервиса, из него собираются короткие ссылки
        self.public_url = os.environ.get("PUBLIC_URL", "http://localhost").rstrip("/")

    @property
    def domain(self) -> str:
        return urlparse(self.public_url).hostname or ""


settings = Settings()
