"""Authentication routes (JWT login)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from reconkit.config import get_settings
from reconkit.database import get_session

from ..middleware.auth import authenticate, create_token, current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(),
                session: AsyncSession = Depends(get_session)):
    user = await authenticate(session, form.username, form.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(user.username), "token_type": "bearer"}


@router.get("/me")
async def me(user=Depends(current_user)):
    return user


@router.get("/config")
async def auth_config():
    """Public: tells the frontend whether auth is required."""
    return {"require_auth": get_settings().require_auth}
