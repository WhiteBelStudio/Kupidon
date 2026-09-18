# КУПИДОН 0.1.0

Telegram Bot + Telegram Mini App для поиска друзей и общения.

КУПИДОН не предназначен для романтического или сексуального общения.

## Архитектура

- `bot/` — Telegram Bot на aiogram
- `api/` — FastAPI API
- `backend/` — SQLite и Telegram WebApp authentication
- `webapp/` — React/Vite Mini App
- `database/migrations/` — схема БД

## Vercel

Mini App подготовлен для отдельного деплоя на Vercel.

Настройки Vercel:

- Root Directory: `webapp`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

Переменная:

```
VITE_API_URL=https://ВАШ-API
```

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
