# КУПИДОН 0.1.0

Telegram Bot + Telegram Mini App для поиска друзей и общения.

КУПИДОН не предназначен для романтического или сексуального общения.

## Состав
- Python 3.12+
- aiogram 3
- FastAPI
- SQLite + aiosqlite
- React + Vite
- Telegram Mini App authentication через initData
- профили, фото, поиск, лайк/пропуск, взаимные совпадения
- блокировки и жалобы
- базовая админ-проверка через ADMIN_IDS

## Запуск
1. Скопируйте .env.example в .env и укажите BOT_TOKEN.
2. Укажите HTTPS WEBAPP_URL для Telegram Mini App.
3. Укажите API_URL и CORS_ORIGINS.
4. Установите Python-зависимости: python -m pip install -r requirements.txt
5. Установите frontend-зависимости: cd webapp && npm install
6. Из корня запустите API: uvicorn api.main:app --host 0.0.0.0 --port 8000
7. В другом терминале запустите бота: python -m bot.main
8. Для Mini App: cd webapp && npm run dev

## Проверка
python -m pytest -q
python -m compileall backend api bot
cd webapp
npm run build

Настоящий .env и секреты не добавляются в Git.
