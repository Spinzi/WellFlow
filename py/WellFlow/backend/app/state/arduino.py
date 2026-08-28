"""
The single source of truth for "what do we currently know about the
Arduino". Written from the SerialManager's background thread, read from
the asyncio event loop (WebSocket handlers) - every access goes through
a lock because those two worlds run concurrently.

Deliberately holds plain dicts/primitives rather than parsing into a
rigid schema, so new sensor fields the Arduino starts sending show up
here (and therefore in the dashboard) without a backend code change.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Literal

from app.config import LOG_HISTORY_SIZE

LogKind = Literal["message", "error", "connection"]


@dataclass
class LogEntry:
    kind: LogKind
    text: str
    ts: float

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "text": self.text, "ts": self.ts}


class ArduinoState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._connected = False
        self._port: str | None = None
        self._last_data: dict[str, Any] = {}
        self._last_message: str | None = None
        self._last_error: str | None = None
        self._last_update_ts: float | None = None
        self._connected_since_ts: float | None = None
        self._log: deque[LogEntry] = deque(maxlen=LOG_HISTORY_SIZE)

    # -- writers (called from the serial thread) -------------------------

    def set_connected(self, port: str) -> None:
        with self._lock:
            self._connected = True
            self._port = port
            self._connected_since_ts = time.time()
            self._push_log("connection", f"Connected to {port}")

    def set_disconnected(self) -> None:
        with self._lock:
            was_connected = self._connected
            self._connected = False
            self._port = None
            self._connected_since_ts = None
            if was_connected:
                self._push_log("connection", "Arduino disconnected")

    def update_data(self, data: dict[str, Any]) -> None:
        with self._lock:
            # Merge rather than replace, so a future partial "data" payload
            # (e.g. only new fields) doesn't wipe out previously known ones.
            merged = dict(self._last_data)
            merged.update({k: v for k, v in data.items() if k != "type"})
            self._last_data = merged
            self._last_update_ts = time.time()

    def set_message(self, message: str) -> None:
        with self._lock:
            self._last_message = message
            self._last_update_ts = time.time()
            self._push_log("message", message)

    def set_error(self, error: str) -> None:
        with self._lock:
            self._last_error = error
            self._last_update_ts = time.time()
            self._push_log("error", error)

    def _push_log(self, kind: LogKind, text: str) -> None:
        # Caller already holds self._lock.
        self._log.append(LogEntry(kind=kind, text=text, ts=time.time()))

    # -- readers -----------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """A JSON-serialisable copy of the full current state."""
        with self._lock:
            uptime = None
            if self._connected_since_ts is not None:
                uptime = time.time() - self._connected_since_ts

            return {
                "type": "state",
                "connected": self._connected,
                "port": self._port,
                "data": dict(self._last_data),
                "lastMessage": self._last_message,
                "lastError": self._last_error,
                "lastUpdate": self._last_update_ts,
                "connectionUptimeSeconds": uptime,
                # Newest entry first - convenient for the dashboard's log feed.
                "log": [entry.to_dict() for entry in reversed(self._log)],
            }


# Single shared instance - imported wherever "the current Arduino state"
# is needed, matching the ArduinoState layer in the architecture diagram.
arduino_state = ArduinoState()
