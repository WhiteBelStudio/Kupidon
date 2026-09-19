import asyncio
from aiogram import Bot,Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from backend.config import get_settings
from backend.database import Database
from bot.handlers import start,admin

async def main():
    settings=get_settings()
    db=Database(settings.database_url, settings.database_path)
    await db.init()
    bot=Bot(settings.bot_token,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp=Dispatcher()
    dp.include_router(start.router)
    dp.include_router(admin.router)
    await bot.set_my_commands([
        BotCommand(command="start",description="Открыть КУПИДОН"),
        BotCommand(command="help",description="Помощь"),
        BotCommand(command="admin",description="Панель администратора"),
    ])
    try: await dp.start_polling(bot,db=db,settings=settings)
    finally: await bot.session.close()

if __name__=="__main__":
    asyncio.run(main())
