export default function LedIndicator({ label, on, tone = "ok" }) {
  return (
    <div className="led-row">
      <div className="led-indicator">
        <span className="led-bulb" data-on={on} data-tone={tone} />
        <span className="field-row__label" style={{ paddingBottom: 0 }}>
          {label}
        </span>
      </div>
      <span className="field-row__value">{on ? "On" : "Off"}</span>
    </div>
  );
}
