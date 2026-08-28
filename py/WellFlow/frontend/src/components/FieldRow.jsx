export default function FieldRow({ label, value, muted = false }) {
  return (
    <div className="field-row">
      <span className="field-row__label">{label}</span>
      <span className={`field-row__value ${muted ? "field-row__value--muted" : ""}`}>
        {value}
      </span>
    </div>
  );
}
