# WellFlow Serial Protocol

Line-delimited JSON over USB serial at **9600 baud**. Every message, in
either direction, is one JSON value terminated by `\n`.

## Arduino → Raspberry Pi

Every message is a JSON **object** with a `type` field. The Pi's protocol
layer (`backend/app/serial/protocol.py`) accepts any well-formed object
with a `type`, even types it doesn't specifically know about yet — new
message types can be added to the Arduino firmware without breaking the
bridge.

### `type: "data"`

Periodic sensor/state snapshot. All fields are optional from the
parser's point of view — new fields are passed through automatically —
but the Arduino sketch currently sends:

```json
{
  "type": "data",
  "button": false,
  "okLed": false,
  "poorWaterLed": false,
  "errorLed": false,
  "distance": 189.336,
  "SRAM": 651,
  "outsideTemp": 28.3,
  "outsideHum": 50
}
```

The Pi merges each `data` message into its in-memory `ArduinoState`
rather than replacing it, so a future payload that only includes some
fields won't erase the others.

### `type: "message"`

Informational text from the Arduino:

```json
{ "type": "message", "message": "Received Serial." }
```

### `type: "err"`

Reported by the Arduino itself (distinct from malformed-JSON errors,
which are detected and logged on the Pi side):

```json
{ "type": "err", "err": "Something went wrong." }
```

## Raspberry Pi → Arduino

Commands are always sent as a JSON **array** of command objects (matching
`processCommands()` in the sketch, which requires a top-level array):

```json
[
  { "type": "command", "command": "set_led", "led": "led_ok", "value": true }
]
```

The Pi never forwards a browser's command unmodified — every command is
validated and rebuilt from scratch against a whitelist in
`backend/app/serial/protocol.py`:

| Command    | Fields                                          | Notes                                  |
| ---------- | ------------------------------------------------ | --------------------------------------- |
| `set_led`  | `led`: `led_ok` \| `led_poor_water` \| `led_err`, `value`: bool | Matches the Arduino's known LED pins |

Adding a new command means: (1) add it to `VALID_COMMANDS`, (2) write a
`_build_<command>()` validator, (3) update this table.

## Browser ↔ Raspberry Pi (WebSocket, `/ws`)

The browser-facing contract is intentionally simpler than the serial
one — the Pi always speaks in terms of full state:

- **Pi → browser**, on connect and after every Arduino message:
  ```json
  {
    "type": "state",
    "connected": true,
    "port": "/dev/ttyACM0",
    "data": { "distance": 189.3, "outsideTemp": 28.3, "...": "..." },
    "lastMessage": "Received Serial.",
    "lastError": null,
    "lastUpdate": 1732650000.12,
    "connectionUptimeSeconds": 842.5,
    "log": [{ "kind": "message", "text": "Received Serial.", "ts": 1732650000.12 }]
  }
  ```
- **Browser → Pi**, a command request:
  ```json
  { "type": "command", "command": "set_led", "led": "led_ok", "value": true }
  ```
- **Pi → browser**, acknowledging that command:
  ```json
  { "type": "ack", "ok": true }
  ```
  or, if validation failed:
  ```json
  { "type": "ack", "ok": false, "error": "unknown or unsupported led: 'led_nuclear'" }
  ```
