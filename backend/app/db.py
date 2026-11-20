"""Пул соединений с PostgreSQL и запросы к таблице links."""
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,  # открывается при старте приложения
)

FIELDS = "code, target_url, clicks, created_at, last_click_at"


def insert_link(conn, code: str, target_url: str) -> dict:
    # Отдельная транзакция (savepoint): при конфликте кода откатывается только она
    with conn.transaction():
        return conn.execute(
            f"INSERT INTO links (code, target_url) VALUES (%s, %s) RETURNING {FIELDS}",
            (code, target_url),
        ).fetchone()


def get_link(conn, code: str) -> dict | None:
    return conn.execute(f"SELECT {FIELDS} FROM links WHERE code = %s", (code,)).fetchone()


def register_click(conn, code: str) -> str | None:
    """Атомарно увеличивает счётчик переходов и возвращает исходную ссылку."""
    row = conn.execute(
        "UPDATE links SET clicks = clicks + 1, last_click_at = now() "
        "WHERE code = %s RETURNING target_url",
        (code,),
    ).fetchone()
    return row["target_url"] if row else None
