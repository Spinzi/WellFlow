import Card from "./Card";
import LedIndicator from "./LedIndicator";
import FieldRow from "./FieldRow";

export default function OutputsCard({ data }) {
  const { okLed, poorWaterLed, errorLed } = data;

  return (
    <Card icon={<BoltIcon />} title="Outputs">
      <LedIndicator label="OK LED" on={!!okLed} tone="ok" />
      <LedIndicator label="Poor water LED" on={!!poorWaterLed} tone="warning" />
      <LedIndicator label="Error LED" on={!!errorLed} tone="error" />
      <FieldRow
        label="Water pump"
        value="Not reported yet"
        muted
      />
    </Card>
  );
}

function BoltIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M13 2 4 14h6l-1 8 9-12h-6l1-8z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}
