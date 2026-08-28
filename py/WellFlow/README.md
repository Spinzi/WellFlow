# WellFlow

A Raspberry Pi water monitoring/control system. An Arduino streams
sensor data over USB serial; the Pi bridges that to a live web
dashboard over WebSockets, supporting any number of simultaneous
browser clients.

```
Arduino ── USB Serial (9600 baud) ── Raspberry Pi ── WebSocket ── Browser(s)
```

## Project layout

```
WellFlow/
├── backend/            FastAPI + pyserial bridge (runs on the Pi)
│   └── app/
│       ├── main.py         FastAPI app + WebSocket endpoint
│       ├── config.py       all tunables (env-overridable)
│       ├── serial/         discovery, protocol, SerialManager
│       ├── websocket/      ConnectionManager (multi-client broadcast)
│       └── state/          ArduinoState (thread-safe source of truth)
├── frontend/            React + Vite dashboard (Material 3-inspired)
│   └── src/
│       ├── components/     cards, gauge, toggle, chips, log feed
│       ├── pages/          Dashboard.jsx
│       ├── services/       websocket.js (reconnecting client)
│       ├── state/          useArduinoState.js hook
│       └── theme/          design tokens + global styles
└── docs/
    └── protocol.md      the Arduino ⇄ Pi ⇄ browser JSON contract
```

## Raspberry Pi setup

1. **Flash the OS and get on the network** (standard Raspberry Pi OS
   setup — not covered here).

2. **Install system prerequisites:**

   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip
   ```

3. **Plug in the Arduino** via USB. No driver setup should be needed for
   most boards (official Arduino, or CH340-based clones); WellFlow
   auto-detects the port, so you don't need to know the device path.

4. **Clone/copy this project onto the Pi**, then set up the backend:

   ```bash
   cd WellFlow/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   sudo usermod -a -G dialout $USER   # only if you get a serial "permission denied"
   ```
   (log out/in once if you had to run the `usermod` line)

5. **Start the backend:**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

   You should see it searching for, then connecting to, the Arduino in
   the logs. Sanity check from another terminal:

   ```bash
   curl http://localhost:8000/health
   ```

6. **Build and serve the frontend.** You can build it on the Pi itself,
   or build it on a dev machine and copy `frontend/dist/` over — either
   way, Node is only needed at build time, not to run the dashboard.

   ```bash
   cd ../frontend
   npm install
   npm run build
   npm run preview -- --port 5173   # or serve dist/ with any static server
   ```

   For active development instead of a production build:

   ```bash
   npm run dev
   ```

7. **Open the dashboard** at `http://<pi-ip>:5173` from any device on the
   same network. Opening it from multiple laptops/phones at once is
   fully supported — every client gets the same live state.

If the browser and the backend aren't on the same host/port (e.g. you're
serving the built frontend from a different machine), copy
`frontend/.env.example` to `.env` and set `VITE_WS_URL` to point at the
Pi, e.g. `ws://raspberrypi.local:8000/ws`.

## How it works

- **Serial interpreter** (`backend/app/serial/`) — auto-discovers the
  Arduino, connects, and reconnects automatically if it's unplugged. It
  runs on its own background thread since `pyserial` blocks; a
  malformed line is logged and dropped rather than crashing anything.
  Full explanation: `backend/README.md`.
- **State layer** (`backend/app/state/arduino.py`) — the single,
  thread-safe source of truth for "what do we currently know about the
  Arduino". Both the serial thread and every WebSocket handler read
  from the same instance.
- **WebSocket server** (`backend/app/websocket/`, `backend/app/main.py`)
  — supports any number of simultaneous browsers. A new client gets the
  current state immediately; a broadcast goes out on every new Arduino
  message; one dropped client never affects the others. Full
  explanation: `backend/README.md`.
- **Dashboard** (`frontend/`) — never fakes state locally: every value
  shown, including toggle positions, reflects what the Arduino last
  actually reported.
- **Protocol** (`docs/protocol.md`) — the full JSON contract in both
  directions, plus how to extend it.

## Development stages (for reference)

The project was built in the order the brief specified:

1. Serial interpreter (`app/serial/`, `app/state/`) — verified standalone
   with `python -m py_compile` and inline protocol unit tests.
2. WebSocket server (`app/websocket/`, `app/main.py`) — verified by
   booting FastAPI and hitting `/health`.
3. Dashboard UI (`frontend/`) — verified with `npm run build`.
4. Dashboard controls wired to real commands (`ControlsCard.jsx` →
   `useArduinoState.sendCommand` → `/ws` → `SerialManager.send_command`).
5. Polish: Material 3-inspired cream/soft-yellow theme, gauge readout,
   log feed, disabled/"coming soon" states for not-yet-implemented
   Arduino features (TDS sensor, pump control).

## Not included yet (by design)

Per the brief: no database, no authentication, no Docker, no systemd
service file. All of these are natural next steps once the core bridge
is proven out, but adding them now would be premature for this stage.

## Extending the protocol

Adding a new Arduino message type or command does **not** require
touching the frontend or the WebSocket layer — see
`docs/protocol.md` and the "Adding a new sensor card later" section of
`frontend/README.md`.
