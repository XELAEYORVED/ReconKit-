"""Scan comparison (diff) route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from reconkit.database import get_session

from .. import services
from ..middleware.auth import current_user

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("/{id1}/{id2}")
async def compare(id1: str, id2: str, session: AsyncSession = Depends(get_session),
                  user=Depends(current_user)):
    try:
        return await services.compare_scans(session, id1, id2)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
