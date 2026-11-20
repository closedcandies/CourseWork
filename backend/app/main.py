"""Сервис сокращения ссылок: REST API и перенаправление по короткому коду."""
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Path, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from psycopg.errors import UniqueViolation

from . import db
from .codes import ALIAS_PATTERN, new_code
from .config import settings
from .schemas import LinkCreate, LinkOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.pool.open(wait=True, timeout=30)  # ждём, пока поднимется PostgreSQL
    yield
    db.pool.close()


app = FastAPI(
    title="Сервис сокращения ссылок",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


def to_out(row: dict) -> LinkOut:
    return LinkOut(short_url=f"{settings.public_url}/{row['code']}", **row)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    """Понятное сообщение об ошибке вместо стандартного списка pydantic."""
    field = next((str(e["loc"][-1]) for e in exc.errors() if e.get("loc")), "")
    if field == "alias":
        msg = "Короткое имя: 3–32 символа (латиница, цифры, «-», «_»), не из зарезервированных"
    elif field == "url":
        msg = "Введите корректную ссылку, начинающуюся с http:// или https://"
    else:
        msg = "Некорректный запрос"
    return JSONResponse(status_code=422, content={"detail": msg})


@app.get("/api/health", tags=["service"])
def health():
    """Проверка работоспособности: приложение и соединение с БД."""
    with db.pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "db": "ok"}


@app.post("/api/links", response_model=LinkOut, status_code=status.HTTP_201_CREATED, tags=["links"])
def create_link(body: LinkCreate):
    """Создать короткую ссылку. Если alias не задан, код генерируется случайно."""
    target = str(body.url)
    if urlparse(target).hostname == settings.domain:
        raise HTTPException(400, "Нельзя сокращать ссылки на сам сервис")

    with db.pool.connection() as conn:
        if body.alias:
            try:
                row = db.insert_link(conn, body.alias, target)
            except UniqueViolation:
                raise HTTPException(409, "Такое короткое имя уже занято")
        else:
            for _ in range(5):  # коллизия маловероятна, но обрабатываем её
                try:
                    row = db.insert_link(conn, new_code(), target)
                    break
                except UniqueViolation:
                    continue
            else:
                raise HTTPException(503, "Не удалось подобрать свободный код, повторите попытку")
    return to_out(row)


@app.get("/api/links/{code}", response_model=LinkOut, tags=["links"])
def link_stats(code: str = Path(pattern=ALIAS_PATTERN)):
    """Информация о ссылке и число переходов."""
    with db.pool.connection() as conn:
        row = db.get_link(conn, code)
    if row is None:
        raise HTTPException(404, "Ссылка не найдена")
    return to_out(row)


NOT_FOUND_PAGE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Ссылка не найдена</title>
<link rel="stylesheet" href="/assets/style.css"></head>
<body><main class="card"><h1>Ссылка не найдена</h1>
<p>Такой короткой ссылки нет или она была введена с ошибкой.</p>
<p><a href="/">Создать новую ссылку</a></p></main></body></html>"""


@app.get("/{code}", include_in_schema=False)
def follow(code: str = Path(pattern=ALIAS_PATTERN)):
    """Перенаправление по короткой ссылке с подсчётом перехода."""
    with db.pool.connection() as conn:
        target = db.register_click(conn, code)
    if target is None:
        return HTMLResponse(NOT_FOUND_PAGE, status_code=404)
    # 302, а не 301: браузер не кэширует перенаправление, и каждый переход учитывается
    return RedirectResponse(target, status_code=302, headers={"Cache-Control": "no-store"})
