import { useEffect, useRef, useState, useCallback } from "react";
import { WellFlowSocket, resolveWsUrl } from "../services/websocket";

const EMPTY_STATE = {
  connected: false,
  port: null,
  data: {},
  lastMessage: null,
  lastError: null,
  lastUpdate: null,
  connectionUptimeSeconds: null,
  log: [],
};

/**
 * Owns one WellFlowSocket for the lifetime of the app and exposes:
 *  - wsStatus: "connecting" | "open" | "closed" — the browser<->Pi link
 *  - arduinoState: the latest full snapshot the Pi reported (source of truth)
 *  - sendCommand: fire a command; never mutates arduinoState locally, so
 *    the UI only ever reflects what the Arduino actually reported back.
 *  - pendingCommandKeys: commands sent but not yet reflected in a new
 *    state snapshot, so controls can show a brief "working on it" state
 *    without faking the result.
 */
export function useArduinoState() {
  const [wsStatus, setWsStatus] = useState("connecting");
  const [arduinoState, setArduinoState] = useState(EMPTY_STATE);
  const [lastAckError, setLastAckError] = useState(null);
  const [pendingCommandKeys, setPendingCommandKeys] = useState(() => new Set());
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = new WellFlowSocket(resolveWsUrl(), {
      onStatusChange: setWsStatus,
      onState: (state) => {
        setArduinoState(state);
        setPendingCommandKeys(new Set());
      },
      onAck: (ack) => {
        if (!ack.ok) setLastAckError(ack.error || "Command rejected");
      },
    });
    socketRef.current = socket;
    socket.connect();

    return () => socket.close();
  }, []);

  const sendCommand = useCallback((command, pendingKey) => {
    const sent = socketRef.current?.sendCommand(command);
    if (sent && pendingKey) {
      setPendingCommandKeys((prev) => new Set(prev).add(pendingKey));
    }
    return sent;
  }, []);

  return { wsStatus, arduinoState, sendCommand, pendingCommandKeys, lastAckError };
}
