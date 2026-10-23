"""ReconKit FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from reconkit import ETHICAL_BANNER, __version__
from reconkit.config import apply_api_key, get_settings
from reconkit.database import init_db, session_scope
from reconkit.models import ApiKey
from reconkit.utils import crypto

from .middleware.auth import bootstrap_admin
from .middleware.cors import setup_cors
from .routes import auth, compare, reports, results, scans, ws



async def _load_db_keys() -> None:
    """Apply API keys stored in the DB onto the live settings + env."""
    async with session_scope() as session:
        rows = (await session.execute(select(ApiKey))).scalars().all()
    for row in rows:
        plain = crypto.decrypt(row.key_encrypted)
        if plain:
            apply_api_key(row.service, plain)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with session_scope() as session:
        await bootstrap_admin(session)
    await _load_db_keys()
    yield


app = FastAPI(
    title="ReconKit API",
    version=__version__,
    description="Passive OSINT reconnaissance. " + ETHICAL_BANNER,
    lifespan=lifespan,
)

setup_cors(app)

for module in (auth, scans, results, reports, compare):
    app.include_router(module.router)
app.include_router(ws.router)


@app.middleware("http")
async def ethical_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-ReconKit-Notice"] = "Passive OSINT only - responsible use"
    return response


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": __version__, "banner": ETHICAL_BANNER}


# --- Serve the built frontend (if present) ---------------------------------
_WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
if _WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_WEB_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        index = _WEB_DIST / "index.html"
        return FileResponse(index)
else:
    @app.get("/")
    async def root():
        return {
            "name": "ReconKit API",
            "version": __version__,
            "banner": ETHICAL_BANNER,
            "docs": "/docs",
            "note": "Frontend not built. Run `npm install && npm run build` in ./web.",
        }
