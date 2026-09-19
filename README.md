<!-- Vercel deployment trigger: FastAPI function fix 2026-09-19 -->

# КУПИДОН 0.2.0

Telegram Bot + Telegram Mini App для поиска друзей и общения.

КУПИДОН не предназначен для романтического или сексуального общения.

## Архитектура

- `bot/` — Telegram Bot на aiogram
- `api/` — FastAPI API
- `backend/` — PostgreSQL/SQLite database adapter и Telegram WebApp authentication
- `webapp/` — React/Vite Mini App
- `database/migrations/` — схема БД

## Vercel

Mini App подключён к GitHub-репозиторию `WhiteBelStudio/Kupidon` и деплоится на Vercel из ветки `main`. Backend и Mini App используют Neon PostgreSQL.

Для production frontend API использует same-origin `/api` и `/media`.

## Backend

Backend запускается отдельно:

```bash
python -m pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
python -m bot.main
```

Секреты и настоящий `.env` в GitHub не добавляются.
