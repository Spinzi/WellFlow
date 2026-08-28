"""
WellFlow backend entrypoint.

    SerialManager  -->  ArduinoState  -->  ConnectionManager  -->  browsers
   (background thread)   (thread-safe)      (asyncio, this loop)

The SerialManager runs on its own thread because pyserial blocks. When it
parses a message it calls `_on_arduino_message`, which is the *only*
bridge between that thread and this asyncio event loop: it schedules a
broadcast via `run_coroutine_threadsafe`. Everything downstream of that
is normal asyncio.

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ALLOW_ORIGINS, HOST, LOG_LEVEL, PORT
from app.serial.manager import SerialManager
from app.serial.protocol import ParsedMessage, ProtocolError
from app.state.arduino import arduino_state
from app.websocket.manager import connection_manager

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("wellflow.main")

app = FastAPI(title="WellFlow Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set once on startup, from inside the running event loop.
_loop: asyncio.AbstractEventLoop | None = None


def _on_arduino_message(_parsed: ParsedMessage) -> None:
    """
    Called from the SerialManager's background thread whenever a new
    message arrives from the Arduino. Must not touch asyncio objects
    directly - only ever hand work to the loop via run_coroutine_threadsafe.

    We broadcast the *full* current snapshot (not just the one message
    that triggered this) so every client always holds a complete,
    self-consistent picture rather than having to merge a stream of
    partial updates.
    """
    if _loop is None:
        return
    message = arduino_state.snapshot()
    asyncio.run_coroutine_threadsafe(connection_manager.broadcast(message), _loop)


serial_manager = SerialManager(on_message=_on_arduino_message)


@app.on_event("startup")
async def on_startup() -> None:
    global _loop
    _loop = asyncio.get_running_loop()
    serial_manager.start()
    logger.info("WellFlow backend listening on %s:%s", HOST, PORT)


@app.get("/health")
async def health() -> dict:
    """Plain REST diagnostic endpoint - useful for quick checks without opening a WebSocket."""
    return {
        "status": "ok",
        "connectedClients": connection_manager.client_count,
        **arduino_state.snapshot(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await connection_manager.connect(websocket)

    # A newly connected client gets the latest known state immediately,
    # even if the Arduino hasn't produced anything new since it joined.
    await connection_manager.send_personal(websocket, arduino_state.snapshot())

    try:
        while True:
            raw = await websocket.receive_json()
            await _handle_client_message(websocket, raw)
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001 - one misbehaving client must not affect anyone else
        logger.exception("Error handling message from client")
    finally:
        await connection_manager.disconnect(websocket)


async def _handle_client_message(websocket: WebSocket, raw: object) -> None:
    """
    Every inbound browser message is treated as an untrusted command
    request - it is validated by the protocol layer and only ever
    forwarded to the Arduino if it matches a known, whitelisted shape.
    """
    if not isinstance(raw, dict) or raw.get("type") != "command":
        await connection_manager.send_personal(
            websocket,
            {"type": "ack", "ok": False, "error": "Expected {\"type\": \"command\", ...}"},
        )
        return

    try:
        serial_manager.send_command(raw)
    except ProtocolError as exc:
        await connection_manager.send_personal(
            websocket, {"type": "ack", "ok": False, "error": str(exc)}
        )
        return

    await connection_manager.send_personal(websocket, {"type": "ack", "ok": True})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
