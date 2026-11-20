# Сервис сокращения ссылок

Веб-приложение для создания коротких ссылок со счётчиком переходов. Работает в Docker:
frontend, backend и PostgreSQL стоят за [nginx-proxy](https://github.com/nginx-proxy/nginx-proxy),
HTTPS-сертификаты Let's Encrypt выпускает и продлевает [acme-companion](https://github.com/nginx-proxy/acme-companion).

Демо: https://link.maicourse.ru

## Возможности

- короткая ссылка из случайного кода (`/eKK0Pm`) или своего имени (`/my-link`);
- перенаправление по короткой ссылке (HTTP 302) с подсчётом переходов;
- список «Мои ссылки» со статистикой в браузере;
- REST API с документацией Swagger: `/api/docs`;
- проверка входных данных, ограничение частоты создания ссылок (10 в минуту с одного IP);
- HTTPS с автоматическим выпуском и продлением сертификата.

## Архитектура

```
Интернет ──:80/:443──► nginx-proxy ──(сеть proxy)──► frontend ──(сеть backend, internal)──► backend ──► db
                            ▲                         nginx:          FastAPI               PostgreSQL
                     acme-companion                   статика,
                     (Let's Encrypt)                  /api, /<код>
```

| Сервис | Образ | Назначение |
|---|---|---|
| `nginx-proxy` | [nginxproxy/nginx-proxy:1.6](https://hub.docker.com/r/nginxproxy/nginx-proxy) | обратный прокси, TLS, редирект HTTP → HTTPS |
| `acme-companion` | [nginxproxy/acme-companion:2.5](https://hub.docker.com/r/nginxproxy/acme-companion) | выпуск и продление сертификатов Let's Encrypt |
| `frontend` | свой, на базе [nginx:1.27-alpine](https://hub.docker.com/_/nginx) | веб-интерфейс, проксирование `/api` и коротких ссылок в backend |
| `backend` | свой, на базе [python:3.12-slim](https://hub.docker.com/_/python) | REST API на FastAPI, перенаправления |
| `db` | [postgres:16-alpine](https://hub.docker.com/_/postgres) | хранение ссылок и статистики |

Наружу открыты только порты 80 и 443 у `nginx-proxy`. Сеть `backend` внутренняя: у backend и БД нет выхода в интернет,
и из сети `proxy` они недоступны.

## Требования

- Linux-сервер с Docker Engine 24+ и Docker Compose v2;
- домен с A-записью на IP сервера;
- свободные порты 80 и 443.

## Быстрый старт

```bash
git clone <адрес репозитория> shortener && cd shortener
cp .env.example .env        # указать DOMAIN и POSTGRES_PASSWORD
docker compose up -d --build
```

Через 1–2 минуты сервис будет доступен по `https://<DOMAIN>`: acme-companion получит сертификат автоматически.
Ход выпуска можно смотреть командой `docker logs -f shortener-acme`.

## Переменные окружения (`.env`)

| Переменная | Обязательна | Описание |
|---|---|---|
| `DOMAIN` | да | домен сервиса, например `link.example.com` |
| `POSTGRES_PASSWORD` | да | пароль пользователя PostgreSQL |
| `LETSENCRYPT_EMAIL` | нет | почта для аккаунта Let's Encrypt |

## API

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/links` | создать ссылку: `{"url": "https://…", "alias": "необязательно"}` → `201` |
| `GET` | `/api/links/{code}` | информация о ссылке и число переходов |
| `GET` | `/{code}` | перенаправление (`302`) на исходный адрес |
| `GET` | `/api/health` | проверка работоспособности (приложение и БД) |
| `GET` | `/api/docs` | документация Swagger UI |

Пример:

```bash
curl -X POST https://link.example.com/api/links \
     -H 'Content-Type: application/json' \
     -d '{"url": "https://docs.docker.com/compose/", "alias": "compose"}'
```

## Структура проекта

```
docker-compose.yaml     весь стек
.env.example            пример настроек
backend/                FastAPI-приложение (Dockerfile, app/, tests/)
frontend/               веб-интерфейс и конфиг nginx (Dockerfile, nginx.conf, public/)
db/init.sql             схема БД, применяется при первом запуске
```

## Тесты

```bash
docker run --rm -v "$PWD/backend:/src" -w /src python:3.12-slim \
  sh -c "pip install -r requirements.txt -r requirements-dev.txt && pytest -q"
```

## Обслуживание

```bash
docker compose ps                         # состояние контейнеров
docker compose logs -f backend            # логи приложения
docker compose pull --ignore-buildable && docker compose up -d --build   # обновление
docker compose exec db pg_dump -U shortener shortener > backup.sql   # резервная копия БД
```

Сертификаты продлеваются автоматически: acme-companion раз в час проверяет срок действия.
