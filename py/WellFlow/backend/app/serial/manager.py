"""
Owns the one and only connection to the Arduino.

pyserial is a blocking API, so this runs its read loop in a dedicated
background thread rather than on the asyncio event loop. It talks to
the rest of the app (the WebSocket layer) only through a plain callback
- this module has no asyncio imports and doesn't know FastAPI exists,
so it can be reused or tested completely headless.

Responsibilities:
  - discover the Arduino's serial port
  - connect, and reconnect automatically if it disappears
  - read + parse incoming JSON lines without crashing on bad input
  - keep ArduinoState up to date
  - validate and write outgoing commands
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable

import serial

from app.config import (
    BAUD_RATE,
    PORT_SCAN_INTERVAL_SECONDS,
    RECONNECT_DELAY_SECONDS,
    SERIAL_READ_TIMEOUT,
)
from app.serial.discovery import find_arduino_port
from app.serial.protocol import (
    MSG_TYPE_DATA,
    MSG_TYPE_ERROR,
    MSG_TYPE_MESSAGE,
    ParsedMessage,
    ProtocolError,
    build_arduino_command,
    parse_arduino_line,
)
from app.state.arduino import arduino_state

logger = logging.getLogger("wellflow.serial")

OnMessage = Callable[[ParsedMessage], None]


class SerialManager:
    """
    Call `start()` once (from the main thread, e.g. on app startup).
    `send_command()` is safe to call from any thread once running -
    typically from an asyncio WebSocket handler on the event-loop thread.
    """

    def __init__(self, on_message: OnMessage | None = None) -> None:
        self._on_message = on_message
        self._serial: serial.Serial | None = None
        # pyserial isn't guaranteed thread-safe for concurrent read+write;
        # reads only ever happen on our own background thread, but writes
        # can come from the asyncio thread, so guard those explicitly.
        self._write_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # -- lifecycle ------------------------------------------------------

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="SerialManager", daemon=True)
        self._thread.start()
        logger.info("SerialManager started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:  # noqa: BLE001 - shutting down, best effort only
                pass

    # -- public API -------------------------------------------------------

    def send_command(self, command: dict[str, Any]) -> None:
        """
        Validate, serialize, and write a single command to the Arduino.
        Raises ProtocolError for anything that fails validation or if the
        Arduino isn't currently connected - callers (the WebSocket
        handler) are expected to turn that into a response to the
        browser, never to crash on it.
        """
        payload = build_arduino_command(command)  # raises ProtocolError on bad input

        ser = self._serial
        if ser is None or not ser.is_open:
            raise ProtocolError("Arduino is not connected")

        line = json.dumps(payload) + "\n"
        with self._write_lock:
            ser.write(line.encode("utf-8"))

    # -- internals: the background thread's own loop ----------------------

    def _run(self) -> None:
        logger.info("Searching for Arduino...")

        while not self._stop_event.is_set():
            port = find_arduino_port()

            if port is None:
                time.sleep(PORT_SCAN_INTERVAL_SECONDS)
                continue

            try:
                self._connect_and_read(port)
            except serial.SerialException as exc:
                logger.warning("Serial connection lost (%s): %s", port, exc)
            except Exception:  # noqa: BLE001 - one bad line/exception must not kill the thread
                logger.exception("Unexpected error in serial loop")
            finally:
                arduino_state.set_disconnected()
                self._serial = None

            if not self._stop_event.is_set():
                time.sleep(RECONNECT_DELAY_SECONDS)

    def _connect_and_read(self, port: str) -> None:
        logger.info("Connecting to %s...", port)
        with serial.Serial(port, BAUD_RATE, timeout=SERIAL_READ_TIMEOUT) as ser:
            self._serial = ser
            arduino_state.set_connected(port)
            logger.info("Connected to %s", port)

            while not self._stop_event.is_set():
                # If the device is unplugged mid-read, pyserial raises
                # SerialException here, which bubbles up to _run() and
                # triggers the reconnect loop above.
                raw_line = ser.readline()
                if not raw_line:
                    continue  # readline() just timed out - normal, keep looping
                self._handle_line(raw_line)

    def _handle_line(self, raw_line: bytes) -> None:
        text = raw_line.decode("utf-8", errors="replace").strip()
        if not text:
            return

        try:
            parsed = parse_arduino_line(text)
        except ProtocolError as exc:
            # A malformed line is a fact about the Arduino's output, not a
            # bug in this process - log it, surface it to the dashboard,
            # and move on to the next line.
            logger.warning("Dropping malformed serial line (%s): %r", exc, text)
            arduino_state.set_error(f"Malformed message from Arduino: {exc}")
            return

        if parsed.type == MSG_TYPE_DATA:
            arduino_state.update_data(parsed.raw)
        elif parsed.type == MSG_TYPE_MESSAGE:
            arduino_state.set_message(str(parsed.raw.get("message", "")))
        elif parsed.type == MSG_TYPE_ERROR:
            arduino_state.set_error(str(parsed.raw.get("err", "")))
        else:
            # Unknown-but-well-formed type: the Arduino protocol has grown
            # ahead of this codebase. Don't drop it - just note it and let
            # subscribers see it via the raw message if they care to.
            logger.info("Unhandled message type from Arduino: %s", parsed.type)

        self._emit(parsed)

    def _emit(self, parsed: ParsedMessage) -> None:
        if self._on_message is not None:
            self._on_message(parsed)
