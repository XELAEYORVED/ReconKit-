"""Scan CRUD + launch routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from reconkit.database import get_session
from reconkit.modules import get_registry

from .. import services
from ..middleware.auth import current_user
from ..realtime import manager

router = APIRouter(prefix="/api/scans", tags=["scans"])


class ScanCreate(BaseModel):
    target: str = Field(..., min_length=1, max_length=512)
    modules: list[str] | None = None
    target_type: str | None = None


@router.post("", status_code=202)
async def create_scan(body: ScanCreate, user=Depends(current_user)):
    """Launch a passive scan. Returns the scan id; progress streams over WS."""
    try:
        scan_id = await manager.launch(body.target, body.modules, body.target_type)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"scan_id": scan_id, "status": "running",
            "ws": f"/ws/scan/{scan_id}"}


@router.get("")
async def list_scans(
    limit: int = Query(50, le=200), offset: int = 0,
    target: str | None = None,
    session: AsyncSession = Depends(get_session), user=Depends(current_user),
):
    return await services.list_scans(session, limit=limit, offset=offset, target=target)


@router.get("/stats")
async def stats(session: AsyncSession = Depends(get_session), user=Depends(current_user)):
    return await services.dashboard_stats(session)


@router.get("/modules")
async def modules(user=Depends(current_user)):
    reg = get_registry()
    out = []
    for name in sorted(reg):
        m = reg[name]()
        out.append({
            "name": name,
            "description": m.description,
            "category": m.category,
            "supported_types": [t.value for t in m.supported_types],
            "requires_api_key": m.requires_api_key,
            "api_service": m.api_service,
            "available": m.available(),
        })
    return out


@router.get("/{scan_id}")
async def get_scan(scan_id: str, session: AsyncSession = Depends(get_session),
                   user=Depends(current_user)):
    scan = await services.get_scan_dict(session, scan_id, include_results=True)
    if not scan:
        raise HTTPException(404, "Scan not found")
    return scan


@router.get("/{scan_id}/results")
async def get_results(scan_id: str, module: str | None = None,
                      session: AsyncSession = Depends(get_session),
                      user=Depends(current_user)):
    scan = await services.get_scan(session, scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found")
    results = [r.to_dict() for r in scan.results]
    if module:
        results = [r for r in results if r["module_name"] == module]
    return {"scan_id": scan_id, "results": results}


@router.get("/{scan_id}/graph")
async def get_graph(scan_id: str, session: AsyncSession = Depends(get_session),
                    user=Depends(current_user)):
    scan = await services.get_scan(session, scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found")
    return (scan.summary or {}).get("graph", {"nodes": [], "edges": []})


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(scan_id: str, session: AsyncSession = Depends(get_session),
                      user=Depends(current_user)):
    ok = await services.delete_scan(session, scan_id)
    if not ok:
        raise HTTPException(404, "Scan not found")
