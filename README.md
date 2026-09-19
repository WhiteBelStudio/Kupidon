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

Настройки Vercel:

- Root Directory: `webapp`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

Для production frontend API использует same-origin `/api` и `/media`. Для dev можно использовать `VITE_DEV_TELEGRAM_ID`.

Полученный HTTPS URL указывается как `WEBAPP_URL` для backend/bot.

## Backend

Backend запускается отдельно:

```bash
python -m pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
python -m bot.main
```

## Проверка

```bash
python -m compileall backend api bot
python -m pytest -q
cd webapp
npm install
npm run build
```

Секреты и настоящий `.env` в GitHub не добавляются.

<!-- Vercel deployment trigger: 2026-09-19 -->
