"""
Arduino auto-discovery.

Deliberately has no notion of "the" port - it just answers "what looks
like an Arduino right now?" each time it's called, so SerialManager can
call it in a loop and pick up a board that was plugged in after startup.
"""
from __future__ import annotations

import serial.tools.list_ports

from app.config import ARDUINO_PORT_HINTS


def find_arduino_port() -> str | None:
    """
    Scan currently visible serial ports and return the device path
    (e.g. '/dev/ttyACM0') of the first one that looks like an Arduino,
    or None if nothing matches.

    Matching is heuristic on purpose: Arduino-compatible boards show up
    under many different USB-serial chip names (CH340, FTDI, the official
    Arduino "usbmodem" style, etc), so there's no single reliable field
    to key off. If the Pi ever has more than one serial device attached,
    the hint list can be tightened or made configurable.
    """
    for port in serial.tools.list_ports.comports():
        description = (port.description or "").lower()
        manufacturer = (port.manufacturer or "").lower()

        if any(
            hint in description or hint in manufacturer
            for hint in ARDUINO_PORT_HINTS
        ):
            return port.device

    return None


def list_serial_ports() -> list[dict[str, str]]:
    """All currently visible serial ports, for logging/diagnostics."""
    return [
        {
            "device": port.device,
            "description": port.description or "",
            "manufacturer": port.manufacturer or "",
        }
        for port in serial.tools.list_ports.comports()
    ]
