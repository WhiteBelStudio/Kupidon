import hashlib,hmac,json,time
from urllib.parse import parse_qsl

class TelegramAuthError(ValueError):
    pass

def validate_init_data(init_data: str, bot_token: str, max_age: int = 86400) -> dict:
    if not init_data:
        raise TelegramAuthError("Missing Telegram initData")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if not received:
        raise TelegramAuthError("Missing Telegram hash")
    check = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise TelegramAuthError("Invalid Telegram initData")
    try:
        auth_date = int(pairs.get("auth_date","0"))
    except ValueError as exc:
        raise TelegramAuthError("Invalid auth_date") from exc
    if not auth_date or time.time() - auth_date > max_age:
        raise TelegramAuthError("Expired Telegram initData")
    try:
        return json.loads(pairs["user"])
    except (KeyError,json.JSONDecodeError) as exc:
        raise TelegramAuthError("Invalid Telegram user data") from exc
