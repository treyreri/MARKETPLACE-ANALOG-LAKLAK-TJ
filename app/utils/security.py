from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.config import settings
password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


_dummy_hash: str | None = None


def burn_password_check(plain_password: str) -> None:
    """Spend the same time as a real check when the user does not exist,
    so response time does not reveal which phone numbers are registered."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("dummy-password-for-timing")
    verify_password(plain_password, _dummy_hash)

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm] )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None