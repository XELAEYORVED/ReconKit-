"""JWT authentication for the ReconKit API.

Multi-user via a ``users`` table. An admin user is bootstrapped from
``RECONKIT_ADMIN_USER`` / ``RECONKIT_ADMIN_PASSWORD`` on first run. Auth is
*optional*: when ``RECONKIT_REQUIRE_AUTH`` is false (the default) the API runs
open for local single-user use, but the full JWT machinery is available.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reconkit.config import get_settings
from reconkit.database import get_session
from reconkit.models import User

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    # bcrypt operates on at most 72 bytes; truncate explicitly for safety.
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def create_token(username: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def bootstrap_admin(session: AsyncSession) -> None:
    settings = get_settings()
    existing = (await session.execute(
        select(User).where(User.username == settings.admin_user))).scalar_one_or_none()
    if existing is None:
        session.add(User(
            username=settings.admin_user,
            password_hash=hash_password(settings.admin_password),
            is_admin=True,
        ))
        await session.commit()


async def authenticate(session: AsyncSession, username: str, password: str) -> User | None:
    user = (await session.execute(
        select(User).where(User.username == username))).scalar_one_or_none()
    if user and verify_password(password, user.password_hash):
        return user
    return None


async def current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Dependency returning the current user, or an anonymous one if auth is off."""
    settings = get_settings()
    if not settings.require_auth:
        return {"username": "anonymous", "is_admin": True, "auth": False}
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    username = decode_token(token)
    if not username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = (await session.execute(
        select(User).where(User.username == username))).scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return {"username": user.username, "is_admin": user.is_admin, "auth": True}
