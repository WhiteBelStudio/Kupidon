# КУПИДОН Mini App

React/Vite Telegram Mini App.

## Vercel

Подключите GitHub-репозиторий `WhiteBelStudio/Kupidon`.

- Root Directory: `webapp`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

Environment Variable:

```
VITE_API_URL=https://ВАШ-API
```

После деплоя Vercel выдаст HTTPS-адрес. Его нужно указать как `WEBAPP_URL` в backend/bot окружении.

Локальная проверка:

```bash
npm install
npm run build
npm run dev
```
