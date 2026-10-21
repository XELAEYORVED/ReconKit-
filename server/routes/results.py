"""Settings routes: API-key management and runtime config.

(The per-scan results endpoints live under /api/scans/{id}/results in
``scans.py``; this module handles the Settings page needs.)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reconkit.config import get_settings
from reconkit.database import get_session
from reconkit.models import ApiKey
from reconkit.modules import get_registry
from reconkit.utils import crypto

from ..middleware.auth import current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Services whose keys can be managed from the UI.
SERVICES = ["shodan", "virustotal", "abuseipdb", "hunter", "otx",
            "github", "google_cse", "ipinfo", "hibp"]


class ApiKeyIn(BaseModel):
    service: str
    key: str


@router.get("/api-keys")
async def list_keys(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    rows = (await session.execute(select(ApiKey))).scalars().all()
    stored = {r.service for r in rows}
    settings = get_settings()
    out = []
    for svc in SERVICES:
        in_env = bool(settings.api_key_for(svc))
        out.append({
            "service": svc,
            "configured": svc in stored or in_env,
            "source": "database" if svc in stored else ("env" if in_env else None),
        })
    return out


@router.put("/api-keys")
async def set_key(body: ApiKeyIn, session: AsyncSession = Depends(get_session),
                  user=Depends(current_user)):
    existing = (await session.execute(
        select(ApiKey).where(ApiKey.service == body.service))).scalar_one_or_none()
    enc = crypto.encrypt(body.key)
    if existing:
        existing.key_encrypted = enc
    else:
        session.add(ApiKey(service=body.service, key_encrypted=enc))
    return {"service": body.service, "configured": True}


@router.delete("/api-keys/{service}", status_code=204)
async def delete_key(service: str, session: AsyncSession = Depends(get_session),
                     user=Depends(current_user)):
    existing = (await session.execute(
        select(ApiKey).where(ApiKey.service == service))).scalar_one_or_none()
    if existing:
        await session.delete(existing)


@router.get("/modules")
async def module_availability(user=Depends(current_user)):
    reg = get_registry()
    return [
        {
            "name": n, "category": reg[n]().category,
            "requires_api_key": reg[n]().requires_api_key,
            "available": reg[n]().available(),
        }
        for n in sorted(reg)
    ]
