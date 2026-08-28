"""
Tracks every connected browser and fans messages out to all of them.

Knows nothing about serial ports or the Arduino protocol - it only
speaks already-built, JSON-safe dicts. That separation is what lets the
serial side and the websocket side be developed, reasoned about, and
tested independently.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("wellflow.websocket")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("Client connected (%d total)", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("Client disconnected (%d total)", len(self._connections))

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        try:
            await websocket.send_json(message)
        except Exception:  # noqa: BLE001 - a dead socket here shouldn't raise into the caller
            logger.warning("Failed to send to a client; dropping it", exc_info=True)
            await self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """
        Send `message` to every connected client. A client that has gone
        away (closed tab, dropped wifi, etc) is dropped silently - one
        dead socket must never prevent delivery to the others.
        """
        async with self._lock:
            targets = list(self._connections)

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)
            logger.info("Dropped %d dead client(s) during broadcast", len(dead))

    @property
    def client_count(self) -> int:
        return len(self._connections)


# Single shared instance used by the WebSocket endpoint and the serial
# bridge callback in main.py.
connection_manager = ConnectionManager()
