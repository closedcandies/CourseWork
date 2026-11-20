"""Генерация и проверка коротких кодов."""
import re
import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # 62 символа
CODE_LENGTH = 6                                  # 62^6 ≈ 5,7·10^10 вариантов

ALIAS_PATTERN = r"^[A-Za-z0-9_-]{3,32}$"
ALIAS_RE = re.compile(ALIAS_PATTERN)

# Пути, которые занимает сам сервис и которые нельзя отдать под короткую ссылку
RESERVED = {"api", "assets", "healthz", "favicon.svg", "favicon.ico", "robots.txt", "index.html"}


def new_code(length: int = CODE_LENGTH) -> str:
    """Случайный код из латинских букв и цифр (криптостойкий генератор)."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def is_valid_alias(alias: str) -> bool:
    return bool(ALIAS_RE.fullmatch(alias)) and alias.lower() not in RESERVED
