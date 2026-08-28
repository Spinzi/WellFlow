import Card from "./Card";
import ToggleSwitch from "./ToggleSwitch";

const LED_CONTROLS = [
  { key: "led_ok", dataField: "okLed", label: "OK LED", hint: "Normal operation indicator" },
  { key: "led_poor_water", dataField: "poorWaterLed", label: "Poor water LED", hint: "Low water-quality warning" },
  { key: "led_err", dataField: "errorLed", label: "Error LED", hint: "Fault indicator" },
];

export default function ControlsCard({ arduinoState, sendCommand, pendingCommandKeys }) {
  const { connected, data } = arduinoState;

  return (
    <Card icon={<SlidersIcon />} title="Controls">
      {LED_CONTROLS.map(({ key, dataField, label, hint }) => (
        <ToggleSwitch
          key={key}
          label={label}
          hint={hint}
          checked={!!data[dataField]}
          pending={pendingCommandKeys.has(key)}
          disabled={!connected}
          onChange={(nextValue) =>
            sendCommand({ command: "set_led", led: key, value: nextValue }, key)
          }
        />
      ))}
      {!connected && (
        <p style={{ fontSize: 12, color: "var(--color-text-faint)" }}>
          Controls are disabled until the Arduino is connected.
        </p>
      )}
    </Card>
  );
}

function SlidersIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M4 6h16M4 12h16M4 18h16"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <circle cx="9" cy="6" r="2" fill="var(--color-surface)" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="16" cy="12" r="2" fill="var(--color-surface)" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="10" cy="18" r="2" fill="var(--color-surface)" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}
