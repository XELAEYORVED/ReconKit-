"""Report download + export routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from reconkit import export as exporter
from reconkit import report as reporter
from reconkit.database import get_session

from .. import services
from ..middleware.auth import current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])

_EXT = {"markdown": "md", "md": "md", "json": "json", "html": "html",
        "pdf": "pdf", "csv": "csv", "stix": "json", "misp": "json"}


@router.get("/{scan_id}")
async def download_report(scan_id: str, format: str = "json",
                          session: AsyncSession = Depends(get_session),
                          user=Depends(current_user)):
    scan = await services.get_scan_dict(session, scan_id, include_results=True)
    if not scan:
        raise HTTPException(404, "Scan not found")
    fmt = format.lower()
    try:
        if fmt in ("json", "md", "markdown", "html", "pdf"):
            content, media = reporter.render(scan, fmt)
        elif fmt in ("csv", "stix", "misp"):
            content, media = exporter.export(scan, fmt)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    ext = _EXT.get(fmt, fmt)
    filename = f"reconkit-{scan_id}.{ext}"
    return Response(
        content=content, media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
