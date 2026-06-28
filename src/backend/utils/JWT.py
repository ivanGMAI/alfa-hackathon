from datetime import datetime, timedelta

import bcrypt
from core.config import settings
from jwt import decode, encode
from pytz import utc


def encode_jwt(payload: dict) -> str:
    private_key = settings.jwt.private_key_path.read_text()
    algorithm = settings.jwt.algorithm
    return encode(payload, private_key, algorithm=algorithm)


def decode_jwt(token: str) -> dict:
    public_key = settings.jwt.public_key_path.read_text()
    algorithm = settings.jwt.algorithm
    return decode(token, public_key, algorithms=[algorithm])


def create_access_token(user_id: int, user_email: str) -> str:
    lifetime = settings.jwt.access_token_lifetime_seconds
    now = datetime.now(utc)
    payload = {
        "sub": str(user_id),
        "email": user_email,
        "exp": now + timedelta(seconds=lifetime),
        "iat": now,
    }
    return encode_jwt(payload)


def create_refresh_token(user_id: int, user_email: str) -> str:
    lifetime = settings.jwt.refresh_token_lifetime_seconds
    now = datetime.now(utc)
    payload = {
        "sub": str(user_id),
        "email": user_email,
        "exp": now + timedelta(seconds=lifetime),
        "iat": now,
    }
    return encode_jwt(payload)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def validate_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
