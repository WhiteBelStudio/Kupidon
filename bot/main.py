import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from backend.config import get_settings
from backend.database import Database
from bot.handlers import start, admin


LOGGER = logging.getLogger("KUPIDON")
TELEGRAM_TIMEOUT = 60
TELEGRAM_RETRIES = 5
RETRY_DELAY = 5


def create_bot(settings):
    proxy = (getattr(settings, "telegram_proxy", "") or "").strip()

    if proxy:
        LOGGER.info("Telegram: через прокси")
        session = AiohttpSession(
            proxy=proxy,
            timeout=TELEGRAM_TIMEOUT,
        )
    else:
        LOGGER.warning(
            "Telegram: TELEGRAM_PROXY не задан. "
            "Используется прямое подключение."
        )
        session = AiohttpSession(timeout=TELEGRAM_TIMEOUT)

    return Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def call_with_retry(name, callback):
    last_error = None

    for attempt in range(1, TELEGRAM_RETRIES + 1):
        try:
            LOGGER.info(
                "Telegram %s: попытка %s/%s",
                name,
                attempt,
                TELEGRAM_RETRIES,
            )
            result = await asyncio.wait_for(
                callback(),
                timeout=TELEGRAM_TIMEOUT + 10,
            )
            LOGGER.info("Telegram %s: успешно.", name)
            return result
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            last_error = exc
            LOGGER.warning(
                "Telegram %s: ошибка %s/%s: %s",
                name,
                attempt,
                TELEGRAM_RETRIES,
                exc,
            )
            if attempt < TELEGRAM_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

    raise last_error


async def configure_telegram(bot, settings):
    me = await call_with_retry("getMe", bot.get_me)

    LOGGER.info(
        "Telegram подключен: @%s (ID %s)",
        me.username,
        me.id,
    )

    try:
        await call_with_retry(
            "deleteWebhook",
            lambda: bot.delete_webhook(drop_pending_updates=False),
        )
    except Exception:
        LOGGER.exception("Не удалось удалить webhook.")

    try:
        await call_with_retry(
            "setChatMenuButton",
            lambda: bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🚀 КУПИДОН",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ),
        )
    except Exception:
        LOGGER.exception("Не удалось настроить кнопку Mini App.")

    try:
        await call_with_retry(
            "setMyCommands",
            lambda: bot.set_my_commands(
                [
                    BotCommand(command="start", description="Открыть КУПИДОН"),
                    BotCommand(command="help", description="Помощь"),
                    BotCommand(command="admin", description="Панель администратора"),
                ]
            ),
        )
    except Exception:
        LOGGER.exception("Не удалось установить команды Telegram.")


async def main():
    LOGGER.info("==========================================")
    LOGGER.info("KUPIDON BOT START")
    LOGGER.info("==========================================")
    LOGGER.info("Python: %s", sys.version.replace("\n", " "))

    settings = get_settings()

    if getattr(settings, "telegram_proxy", ""):
        LOGGER.info("TELEGRAM_PROXY: задан")
    else:
        LOGGER.warning("TELEGRAM_PROXY: НЕ ЗАДАН")

    db = Database(settings.database_url, settings.database_path)

    try:
        await asyncio.wait_for(db.init(), timeout=30)
        LOGGER.info("База данных готова.")
    except Exception:
        LOGGER.exception("Ошибка инициализации базы данных.")
        await db.close()
        return

    bot = None

    try:
        bot = create_bot(settings)

        dp = Dispatcher()
        dp.include_router(start.router)
        dp.include_router(admin.router)

        LOGGER.info("Telegram routers подключены.")

        await configure_telegram(bot, settings)

        LOGGER.info("==========================================")
        LOGGER.info("KUPIDON BOT POLLING STARTED")
        LOGGER.info("==========================================")

        await dp.start_polling(
            bot,
            db=db,
            settings=settings,
            polling_timeout=30,
        )

    except asyncio.CancelledError:
        raise
    except Exception:
        LOGGER.exception("Критическая ошибка Telegram-бота.")
    finally:
        await db.close()
        if bot is not None:
            try:
                await bot.session.close()
            except Exception:
                LOGGER.exception("Ошибка закрытия Telegram session.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )
    asyncio.run(main())
