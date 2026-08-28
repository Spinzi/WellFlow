const SIZE = 168;
const STROKE = 12;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
// Gauge sweeps 270° (like an analog dial), leaving a 90° gap at the bottom.
const ARC_FRACTION = 0.75;

export default function GaugeReadout({ value, max = 400, unit = "cm", caption }) {
  const hasValue = typeof value === "number" && !Number.isNaN(value);
  const clamped = hasValue ? Math.min(Math.max(value, 0), max) : 0;
  const fraction = hasValue ? (clamped / max) * ARC_FRACTION : 0;

  const trackDash = `${CIRCUMFERENCE * ARC_FRACTION} ${CIRCUMFERENCE}`;
  const valueDash = `${CIRCUMFERENCE * fraction} ${CIRCUMFERENCE}`;
  // Rotate so the arc starts at the bottom-left and sweeps clockwise.
  const rotation = 135;

  return (
    <div className="gauge">
      <div className="gauge__ring">
        <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="var(--color-surface-sunken)"
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={trackDash}
            transform={`rotate(${rotation} ${SIZE / 2} ${SIZE / 2})`}
          />
          {hasValue && (
            <circle
              cx={SIZE / 2}
              cy={SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke="var(--color-accent-strong)"
              strokeWidth={STROKE}
              strokeLinecap="round"
              strokeDasharray={valueDash}
              transform={`rotate(${rotation} ${SIZE / 2} ${SIZE / 2})`}
              style={{ transition: "stroke-dasharray 400ms var(--ease-standard)" }}
            />
          )}
        </svg>
        <div className="gauge__value">
          <span className="gauge__number">{hasValue ? clamped.toFixed(1) : "—"}</span>
          <span className="gauge__unit">{unit}</span>
        </div>
      </div>
      {caption && <span className="gauge__caption">{caption}</span>}
    </div>
  );
}
