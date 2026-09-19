import hashlib

from fastapi import Header, HTTPException, Request
from backend.database import Database
from backend.telegram_auth import TelegramAuthError, validate_init_data


async def current_user(
    request: Request,
    x_telegram_init_data: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    x_dev_telegram_id: int | None = Header(default=None),
    x_guest_id: str | None = Header(default=None),
) -> dict:
    settings = request.app.state.settings
    db: Database = request.app.state.db

    # Telegram auth is optional now. When Mini App is opened outside Telegram,
    # use a persistent browser guest identity instead of blocking the app.
    init_data = x_telegram_init_data
    if not init_data and authorization:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "tma" and credentials:
            init_data = credentials.strip()

    tg_user = None
    if init_data:
        try:
            tg_user = validate_init_data(init_data, settings.bot_token)
        except TelegramAuthError as exc:
            # Invalid Telegram data must not prevent browser/guest mode.
            tg_user = None

    if tg_user:
        telegram_id = int(tg_user["id"])
        username = tg_user.get("username")
        first_name = tg_user.get("first_name") or "Пользователь"
    elif settings.debug and x_dev_telegram_id and x_dev_telegram_id == settings.dev_telegram_id:
        telegram_id = int(x_dev_telegram_id)
        username = "dev_user"
        first_name = "Dev"
    elif x_guest_id:
        # Convert the browser's random local ID into a stable positive bigint
        # suitable for the existing users.telegram_id database column.
        digest = hashlib.sha256(x_guest_id.encode("utf-8")).hexdigest()
        telegram_id = int(digest[:15], 16)
        username = f"guest_{digest[:10]}"
        first_name = "Гость"
    else:
        # The frontend normally creates X-Guest-Id. Keep a deterministic
        # fallback for direct API calls so the old Telegram 401 is gone.
        digest = hashlib.sha256(b"kupidon-anonymous-browser").hexdigest()
        telegram_id = int(digest[:15], 16)
        username = f"guest_{digest[:10]}"
        first_name = "Гость"

    user = await db.upsert_user(telegram_id, username, first_name)
    if user["is_blocked"]:
        raise HTTPException(403, "Account is blocked")
    return user
