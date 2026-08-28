import Card from "./Card";
import FieldRow from "./FieldRow";
import LogFeed from "./LogFeed";
import StatusChip from "./StatusChip";

export default function SystemCard({ arduinoState }) {
  const { connected, data, lastError, log } = arduinoState;
  const sram = data.SRAM;

  return (
    <Card
      icon={<ChipIcon />}
      title="System"
      headerRight={
        lastError ? (
          <StatusChip tone="warning" label="Recent error" />
        ) : (
          <StatusChip tone="success" label="Nominal" />
        )
      }
    >
      <FieldRow
        label="Communication"
        value={connected ? "Streaming" : "No serial link"}
        muted={!connected}
      />
      <FieldRow
        label="Arduino free SRAM"
        value={typeof sram === "number" ? `${sram} bytes` : "—"}
        muted={typeof sram !== "number"}
      />
      <FieldRow
        label="Last error"
        value={lastError || "None"}
        muted={!lastError}
      />
      <div>
        <div className="field-row__label" style={{ marginBottom: 8 }}>
          Recent activity
        </div>
        <LogFeed entries={log} />
      </div>
    </Card>
  );
}

function ChipIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <rect x="6" y="6" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}
