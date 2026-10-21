"""WebSocket endpoint for realtime scan progress."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..realtime import manager

router = APIRouter()


@router.websocket("/ws/scan/{scan_id}")
async def scan_ws(websocket: WebSocket, scan_id: str):
    await websocket.accept()
    await manager.subscribe(scan_id, websocket)
    try:
        while True:
            # We don't expect client messages, but keep the socket alive and
            # allow a client "ping" to be echoed.
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.unsubscribe(scan_id, websocket)
