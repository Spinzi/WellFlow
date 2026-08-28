# WellFlow Frontend

React + Vite dashboard, styled with a custom Material 3-inspired token
system (no component library) in a warm cream / soft-yellow theme.

## Setup

```bash
cd frontend
npm install
```

## Run (development)

```bash
npm run dev
```

Opens on `http://localhost:5173`. By default it connects to a backend at
`ws://<the page's own hostname>:8000/ws`. If the backend lives elsewhere
(different host, different port), copy `.env.example` to `.env` and set
`VITE_WS_URL`.

## Build for production

```bash
npm run build
```

Output goes to `frontend/dist/` — serve it with any static file server,
or point nginx/Caddy at it on the Pi if you want the dashboard served
locally.

## Structure

- `src/services/websocket.js` — the only file that knows the WebSocket
  wire format; auto-reconnects if the connection drops.
- `src/state/useArduinoState.js` — React hook exposing the live
  connection status, the latest Arduino state snapshot, and
  `sendCommand()`. The UI never fakes state locally — every value shown
  comes from the last snapshot the Pi actually broadcast.
- `src/components/` — presentational pieces (cards, gauge, toggle,
  status chip, log feed).
- `src/pages/Dashboard.jsx` — lays the cards out in the grid.
- `src/theme/` — design tokens (`tokens.css`), global layout
  (`global.css`), and component styles (`components.css`).

## Adding a new sensor card later

1. Add the field to the Arduino's `data` payload (backend needs no
   change — new fields pass straight through to `ArduinoState`).
2. Read it off `arduinoState.data.<field>` in a component.
3. If it deserves its own card, add one under `src/components/` and drop
   it into `src/pages/Dashboard.jsx`'s grid.
