-- Схема БД сервиса сокращения ссылок.
-- Скрипт выполняется образом postgres один раз, при первом запуске с пустым томом.

CREATE TABLE IF NOT EXISTS links (
    id            BIGSERIAL    PRIMARY KEY,
    code          VARCHAR(32)  NOT NULL UNIQUE,      -- короткий код: https://<домен>/<code>
    target_url    TEXT         NOT NULL,             -- исходная длинная ссылка
    clicks        BIGINT       NOT NULL DEFAULT 0,   -- число переходов
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_click_at TIMESTAMPTZ                        -- время последнего перехода
);
