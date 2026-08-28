# WellFlow Backend

Python/FastAPI service that runs on the Raspberry Pi. Bridges the
Arduino's USB serial output to any number of WebSocket-connected
browsers.

## Setup (Raspberry Pi)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If the Pi user isn't already in the `dialout` group (needed for serial
port access), run once and re-login:

```bash
sudo usermod -a -G dialout $USER
```

## Run

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or simply:

```bash
python3 -m app.main
```

Check it's alive:

```bash
curl http://<pi-ip>:8000/health
```

To run automatically on boot, wrap the uvicorn command in a systemd
service (not included yet — intentionally out of scope for this stage,
see the project root README's "Not included yet" section).

## Configuration

All tunables live in `app/config.py` and can be overridden with
environment variables, e.g.:

```bash
WELLFLOW_PORT=9000 WELLFLOW_BAUD_RATE=9600 uvicorn app.main:app --host 0.0.0.0 --port 9000
```

## Architecture

```
SerialManager (background thread, owns the pyserial connection)
      │  parses JSON lines, validates them
      ▼
ArduinoState (thread-safe, in-memory "source of truth")
      │  on every new message, snapshot() is broadcast
      ▼
ConnectionManager (asyncio, tracks every open WebSocket)
      │
      ▼
any number of browser clients on /ws
```

### How the serial interpreter works

`app/serial/manager.py` owns the one and only connection to the
Arduino. Because `pyserial` is a blocking API, it runs its own loop on a
dedicated background thread (never on the asyncio event loop, which
would freeze the WebSocket server while waiting on serial data).

That loop:

1. Calls `find_arduino_port()` (`app/serial/discovery.py`) until a
   matching USB device shows up — no hard-coded `/dev/ttyACM0`.
2. Opens the port and calls `arduino_state.set_connected(port)`.
3. Reads lines in a tight loop. A read timeout just means "try again" —
   it's not an error.
4. Each line is handed to `app/serial/protocol.py`, which parses the
   JSON and does light schema validation. Malformed JSON is logged and
   dropped — one bad line never crashes the process.
5. Valid `data` messages are merged into `ArduinoState`; `message` and
   `err` messages update the log/latest-message fields.
6. If the Arduino is unplugged, `pyserial` raises `SerialException`,
   which is caught, `ArduinoState` is marked disconnected, and the loop
   goes back to step 1 after a short delay — full automatic recovery,
   no restart needed.

Sending a command works the same direction in reverse:
`SerialManager.send_command()` is called from the asyncio thread (inside
the WebSocket handler), but only ever with output that has already
passed through `protocol.build_arduino_command()` — arbitrary browser
JSON is never written to the serial port.

### How multiple WebSocket clients are handled

`app/websocket/manager.py`'s `ConnectionManager` holds a `set` of every
currently-open `WebSocket`. It is completely independent of the serial
layer — it only ever sends/receives plain dicts.

- A new client connecting immediately receives `arduino_state.snapshot()`
  so the dashboard is populated even if the Arduino hasn't sent anything
  since the browser tab opened.
- Every time the SerialManager parses a new Arduino message, it calls a
  callback that schedules `connection_manager.broadcast(...)` onto the
  asyncio event loop via `asyncio.run_coroutine_threadsafe` (this is the
  only bridge between the serial thread and the event loop).
- `broadcast()` iterates every connected client and sends independently;
  if sending to one fails (closed tab, dropped connection) that client is
  quietly removed from the set without affecting anyone else.
- There is exactly one `SerialManager` instance and exactly one open
  serial port, no matter how many browsers are connected.

### Data flow, end to end

```
Arduino (JSON line)
  → SerialManager (thread) reads + parses + validates
  → ArduinoState.update_data() (thread-safe merge)
  → callback schedules ConnectionManager.broadcast(snapshot)
  → every connected browser receives {"type": "state", ...}

Browser (toggle a control)
  → WebSocket sends {"type": "command", "command": "set_led", ...}
  → FastAPI /ws handler validates via protocol.build_arduino_command()
  → SerialManager.send_command() writes JSON array to serial port
  → Arduino applies it, and its next "data" message reflects the change
  → that change reaches the browser the normal way, through the loop above
```

Note the last step: the dashboard toggle doesn't flip itself optimistically
— it waits for the Arduino's own next state report, which is why "don't
fake state locally" is a hard requirement.
