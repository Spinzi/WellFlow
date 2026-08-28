/**
 * A toggle that never fakes its own state. `checked` always comes from
 * the last state the Arduino actually reported; `pending` just dims the
 * control briefly while we wait for that report to catch up after a
 * command was sent, so the person gets feedback without us guessing.
 */
export default function ToggleSwitch({ label, hint, checked, pending, disabled, onChange }) {
  return (
    <div className="toggle">
      <div>
        <div className="toggle__label">{label}</div>
        {hint && <div className="toggle__hint">{hint}</div>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        className="toggle__control"
        data-checked={checked}
        data-pending={pending}
        disabled={disabled}
        onClick={() => onChange(!checked)}
      />
    </div>
  );
}
