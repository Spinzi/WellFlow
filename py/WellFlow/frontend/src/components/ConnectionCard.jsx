import Card from "./Card";
import StatusChip from "./StatusChip";
import FieldRow from "./FieldRow";

function formatUptime(seconds) {
  if (seconds == null) return null;
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

function formatTimestamp(ts) {
  if (!ts) return null;
  return new Date(ts * 1000).toLocaleTimeString();
}

export default function ConnectionCard({ arduinoState, wsStatus }) {
  const { connected, port, lastMessage, lastUpdate, connectionUptimeSeconds } = arduinoState;

  const wsChip =
    wsStatus === "open"
      ? { tone: "success", label: "Live", pulse: true }
      : wsStatus === "connecting"
      ? { tone: "warning", label: "Connecting…" }
      : { tone: "error", label: "Disconnected" };

  return (
    <Card
      icon={<PlugIcon />}
      title="Connection"
      headerRight={
        <StatusChip
          tone={connected ? "success" : "error"}
          label={connected ? "Arduino online" : "Arduino offline"}
          pulse={connected}
        />
      }
    >
      <FieldRow label="Dashboard link" value={<StatusChip {...wsChip} />} />
      <FieldRow
        label="Serial port"
        value={port || "Searching…"}
        muted={!port}
      />
      <FieldRow
        label="Connected for"
        value={connectionUptimeSeconds != null ? formatUptime(connectionUptimeSeconds) : "—"}
        muted={connectionUptimeSeconds == null}
      />
      <FieldRow
        label="Last message"
        value={lastMessage || "None yet"}
        muted={!lastMessage}
      />
      <FieldRow
        label="Last update"
        value={lastUpdate ? formatTimestamp(lastUpdate) : "—"}
        muted={!lastUpdate}
      />
    </Card>
  );
}

function PlugIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M9 2v5M15 2v5M6 9h12l-1 4a5 5 0 01-10 0L6 9zM12 17v5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
