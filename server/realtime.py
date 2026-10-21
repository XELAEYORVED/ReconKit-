"""Realtime scan orchestration and WebSocket broadcast manager.

Launches scans as background asyncio tasks and streams engine progress events
to every WebSocket subscribed to that scan id. Events are buffered so a client
that connects mid-scan still receives the history.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from reconkit.database import init_db, session_scope
from reconkit.engine import ReconEngine
from reconkit.models import Scan, ScanStatus, TargetType
from reconkit.utils.validators import detect_target_type


class ScanManager:
    def __init__(self) -> None:
        self._subs: dict[str, set[WebSocket]] = defaultdict(set)
        self._buffer: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, scan_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[scan_id].add(ws)
            history = list(self._buffer.get(scan_id, []))
        for event in history:
            await ws.send_json(event)

    async def unsubscribe(self, scan_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[scan_id].discard(ws)

    async def _broadcast(self, scan_id: str, event: dict[str, Any]) -> None:
        self._buffer[scan_id].append(event)
        dead = []
        for ws in list(self._subs.get(scan_id, set())):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._subs[scan_id].discard(ws)

    async def launch(self, target: str, modules: list[str] | None,
                     target_type: str | None = None) -> str:
        """Create a pending scan row and start the background task."""
        await init_db()
        tt = TargetType(target_type) if target_type else detect_target_type(target)
        async with session_scope() as session:
            scan = Scan(target=target, target_type=tt, status=ScanStatus.RUNNING,
                        config={"modules": modules or "auto"})
            session.add(scan)
            await session.flush()
            scan_id = scan.id

        self._tasks[scan_id] = asyncio.create_task(
            self._run(scan_id, target, modules, tt)
        )
        return scan_id

    async def _run(self, scan_id: str, target: str, modules: list[str] | None,
                   tt: TargetType) -> None:
        async def cb(event: dict[str, Any]) -> None:
            await self._broadcast(scan_id, {**event, "scan_id": scan_id})

        engine = ReconEngine(progress_cb=cb)
        try:
            await engine.run_scan(target, modules=modules, target_type=tt, scan_id=scan_id)
        except Exception as exc:
            async with session_scope() as session:
                scan = await session.get(Scan, scan_id)
                if scan:
                    scan.status = ScanStatus.FAILED
                    scan.error = str(exc)
            await self._broadcast(scan_id, {
                "event": "scan_error", "scan_id": scan_id, "error": str(exc),
            })
        finally:
            self._tasks.pop(scan_id, None)


manager = ScanManager()
