"""
Central place for every tunable in the backend. Everything has a sane
default for a Raspberry Pi + Arduino setup, and can be overridden with
environment variables without touching code.
"""
import os

# --- Serial ------------------------------------------------------------

BAUD_RATE = int(os.environ.get("WELLFLOW_BAUD_RATE", "9600"))
SERIAL_READ_TIMEOUT = float(os.environ.get("WELLFLOW_SERIAL_TIMEOUT", "1.0"))
RECONNECT_DELAY_SECONDS = float(os.environ.get("WELLFLOW_RECONNECT_DELAY", "2.0"))
PORT_SCAN_INTERVAL_SECONDS = float(os.environ.get("WELLFLOW_SCAN_INTERVAL", "2.0"))

# Keywords used to recognise an Arduino among all serial ports on the Pi.
# Matched case-insensitively against both the port description and the
# reported manufacturer, so this covers official Arduinos, CH340-based
# clones, and generic "USB Serial" adapters.
ARDUINO_PORT_HINTS = (
    "arduino",
    "usb serial",
    "ch340",
    "wch",
    "usb-serial",
)

# How many recent message/error/connection log entries to keep in memory
# for the dashboard's diagnostics panel.
LOG_HISTORY_SIZE = int(os.environ.get("WELLFLOW_LOG_HISTORY_SIZE", "30"))

# --- HTTP / WebSocket server --------------------------------------------

HOST = os.environ.get("WELLFLOW_HOST", "0.0.0.0")
PORT = int(os.environ.get("WELLFLOW_PORT", "8000"))

# Comma separated list, or "*" for any origin (fine for a LAN dashboard;
# tighten this once WellFlow has a fixed deployment origin).
CORS_ALLOW_ORIGINS = os.environ.get("WELLFLOW_CORS_ORIGINS", "*").split(",")

LOG_LEVEL = os.environ.get("WELLFLOW_LOG_LEVEL", "INFO")
