import hashlib,hmac,json,time
from urllib.parse import urlencode
import pytest
from backend.telegram_auth import TelegramAuthError,validate_init_data

def make_init_data(token):
    pairs={"auth_date":str(int(time.time())),"user":json.dumps({"id":123,"first_name":"Test"},separators=(",",":"))}
    check="\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret=hmac.new(b"WebAppData",token.encode(),hashlib.sha256).digest()
    pairs["hash"]=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    return urlencode(pairs)

def test_valid_init_data():
    assert validate_init_data(make_init_data("token"),"token")["id"]==123

def test_invalid_hash():
    with pytest.raises(TelegramAuthError):
        validate_init_data("auth_date=1&user=%7B%7D&hash=bad","token")
