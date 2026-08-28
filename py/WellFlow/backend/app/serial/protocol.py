"""
The JSON contract between the Raspberry Pi and the Arduino.

Nothing in this file touches a serial port, a thread, or a websocket -
it's pure data-in / data-out, which makes it easy to unit test and the
natural place to extend when the Arduino firmware grows new message or
command types.

    Inbound  (Arduino -> Pi):      parse_arduino_line()
    Outbound (Browser -> Pi -> Arduino): build_arduino_command()
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


class ProtocolError(ValueError):
    """Raised when inbound or outbound data doesn't match the protocol."""


# ---------------------------------------------------------------------------
# Inbound messages (Arduino -> Pi)
# ---------------------------------------------------------------------------

MSG_TYPE_DATA = "data"
MSG_TYPE_MESSAGE = "message"
MSG_TYPE_ERROR = "err"

# Every "type" value the Pi currently understands the *meaning* of. Any
# other well-formed message is still accepted and forwarded (see
# ParsedMessage.is_known) so a firmware update that adds new message
# types doesn't break the bridge - it just won't be specially handled
# until the Pi software catches up.
KNOWN_MESSAGE_TYPES = {MSG_TYPE_DATA, MSG_TYPE_MESSAGE, MSG_TYPE_ERROR}


@dataclass
class ParsedMessage:
    type: str
    raw: dict[str, Any]
    is_known: bool = True


def parse_arduino_line(line: str) -> ParsedMessage:
    """
    Parse and lightly validate one line of text read from the Arduino's
    serial output. Raises ProtocolError for anything unsafe to use
    (malformed JSON, wrong shape, missing 'type'). Never raises just
    because a message type is new/unrecognised - the protocol is
    expected to grow.
    """
    line = line.strip()
    if not line:
        raise ProtocolError("empty line")

    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid JSON ({exc})") from exc

    if not isinstance(obj, dict):
        raise ProtocolError("top-level JSON value must be an object")

    msg_type = obj.get("type")
    if not isinstance(msg_type, str) or not msg_type:
        raise ProtocolError("message is missing a string 'type' field")

    if msg_type == MSG_TYPE_DATA:
        _validate_data_message(obj)

    return ParsedMessage(type=msg_type, raw=obj, is_known=msg_type in KNOWN_MESSAGE_TYPES)


def _validate_data_message(obj: dict[str, Any]) -> None:
    """
    Light schema check on 'data' messages, since they drive the live
    dashboard readouts. Only checks the *type* of fields that are
    present - it never requires a field to exist, so new sensors can be
    added to the Arduino payload without any Pi-side changes.
    """
    expected_types: dict[str, type | tuple[type, ...]] = {
        "button": bool,
        "okLed": bool,
        "poorWaterLed": bool,
        "errorLed": bool,
        "distance": (int, float),
        "SRAM": (int, float),
        "outsideTemp": (int, float),
        "outsideHum": (int, float),
    }
    for key, expected in expected_types.items():
        if key in obj and not isinstance(obj[key], expected):
            raise ProtocolError(
                f"field '{key}' has unexpected type {type(obj[key]).__name__}"
            )


# ---------------------------------------------------------------------------
# Outbound commands (Browser -> Pi -> Arduino)
# ---------------------------------------------------------------------------

# Whitelist of LEDs the Arduino firmware actually implements
# (see the `set_led` handling in processCommands() in the sketch).
VALID_LEDS = {"led_ok", "led_poor_water", "led_err"}

# Whitelist of commands the Pi will forward to the Arduino at all. A
# browser can never send arbitrary JSON straight to the Arduino - every
# command must be named here *and* have a matching `_build_*` function
# below. Add both together when the Arduino gains a new command.
VALID_COMMANDS = {"set_led"}


def build_arduino_command(command: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Validate a command dict received from a browser and turn it into the
    JSON array payload the Arduino expects (its processCommands()
    requires a top-level array). Raises ProtocolError if the command is
    unknown or malformed in any way - callers must never fall back to
    forwarding the raw input.
    """
    if not isinstance(command, dict):
        raise ProtocolError("command must be a JSON object")

    cmd = command.get("command")
    if cmd not in VALID_COMMANDS:
        raise ProtocolError(f"unknown or unsupported command: {cmd!r}")

    if cmd == "set_led":
        return [_build_set_led(command)]

    # Unreachable while VALID_COMMANDS only lists 'set_led', but this
    # keeps the function correct as more commands are whitelisted above.
    raise ProtocolError(f"no builder implemented for command: {cmd!r}")


def _build_set_led(command: dict[str, Any]) -> dict[str, Any]:
    led = command.get("led")
    value = command.get("value")

    if led not in VALID_LEDS:
        raise ProtocolError(f"unknown or unsupported led: {led!r}")
    if not isinstance(value, bool):
        raise ProtocolError("'value' must be a boolean")

    return {"type": "command", "command": "set_led", "led": led, "value": value}
