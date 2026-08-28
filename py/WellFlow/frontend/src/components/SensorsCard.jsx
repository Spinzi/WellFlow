import Card from "./Card";
import FieldRow from "./FieldRow";
import GaugeReadout from "./GaugeReadout";

export default function SensorsCard({ data }) {
  const { distance, outsideTemp, outsideHum } = data;

  return (
    <Card icon={<DropletIcon />} title="Sensors">
      <GaugeReadout
        value={typeof distance === "number" ? distance : null}
        max={400}
        unit="cm"
        caption="Water distance"
      />
      <FieldRow
        label="Outside temperature"
        value={typeof outsideTemp === "number" ? `${outsideTemp.toFixed(1)} °C` : "—"}
        muted={typeof outsideTemp !== "number"}
      />
      <FieldRow
        label="Outside humidity"
        value={typeof outsideHum === "number" ? `${outsideHum.toFixed(0)} %` : "—"}
        muted={typeof outsideHum !== "number"}
      />
      <FieldRow label="Water quality (TDS)" value="Not available yet" muted />
    </Card>
  );
}

function DropletIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M12 3s7 7.4 7 12a7 7 0 11-14 0c0-4.6 7-12 7-12z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}
