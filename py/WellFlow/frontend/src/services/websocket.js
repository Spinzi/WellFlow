/**
 * A small reconnecting WebSocket wrapper. This is the only file that
 * knows the wire format the backend speaks (state / ack messages in,
 * command messages out) - everything else in the app talks to it
 * through plain callbacks and a `sendCommand` method.
 */

const RECONNECT_DELAY_MS = 2000;

/** Build the backend WebSocket URL from env, falling back to same-host:8000. */
export function resolveWsUrl() {
  const configured = import.meta.env.VITE_WS_URL;
  if (configured) return configured;

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.hostname || "localhost";
  const port = import.meta.env.VITE_WS_PORT || "8000";
  return `${protocol}//${host}:${port}/ws`;
}

export class WellFlowSocket {
  /**
   * @param {string} url
   * @param {{onStatusChange?: (status: string) => void, onState?: (state: object) => void, onAck?: (ack: object) => void}} handlers
   */
  constructor(url, handlers = {}) {
    this.url = url;
    this.handlers = handlers;
    this.socket = null;
    this.reconnectTimer = null;
    this.closedByUser = false;
  }

  connect() {
    this.closedByUser = false;
    this._open();
  }

  _open() {
    this._setStatus("connecting");
    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.onopen = () => {
      this._setStatus("open");
    };

    socket.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return; // Ignore anything that isn't valid JSON.
      }

      if (payload.type === "state" && this.handlers.onState) {
        this.handlers.onState(payload);
      } else if (payload.type === "ack" && this.handlers.onAck) {
        this.handlers.onAck(payload);
      }
    };

    socket.onclose = () => {
      this._setStatus("closed");
      if (!this.closedByUser) this._scheduleReconnect();
    };

    socket.onerror = () => {
      socket.close();
    };
  }

  _scheduleReconnect() {
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      if (!this.closedByUser) this._open();
    }, RECONNECT_DELAY_MS);
  }

  _setStatus(status) {
    this.handlers.onStatusChange?.(status);
  }

  /** Send a validated-shape command; the backend re-validates regardless. */
  sendCommand(command) {
    if (this.socket?.readyState !== WebSocket.OPEN) return false;
    this.socket.send(JSON.stringify({ type: "command", ...command }));
    return true;
  }

  close() {
    this.closedByUser = true;
    clearTimeout(this.reconnectTimer);
    this.socket?.close();
  }
}
