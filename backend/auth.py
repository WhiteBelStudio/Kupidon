from fastapi import Header,HTTPException,Request
from backend.database import Database
from backend.telegram_auth import TelegramAuthError,validate_init_data

async def current_user(request: Request,x_telegram_init_data: str|None=Header(default=None),x_dev_telegram_id:int|None=Header(default=None)) -> dict:
    settings=request.app.state.settings
    db: Database=request.app.state.db
    if x_telegram_init_data:
        try:
            tg_user=validate_init_data(x_telegram_init_data,settings.bot_token)
        except TelegramAuthError as exc:
            raise HTTPException(401,str(exc)) from exc
    elif settings.debug and x_dev_telegram_id and x_dev_telegram_id==settings.dev_telegram_id:
        tg_user={"id":x_dev_telegram_id,"username":"dev_user","first_name":"Dev"}
    else:
        raise HTTPException(401,"Telegram authorization required")
    user=await db.upsert_user(int(tg_user["id"]),tg_user.get("username"),tg_user.get("first_name") or "Пользователь")
    if user["is_blocked"]:
        raise HTTPException(403,"Account is blocked")
    return user
