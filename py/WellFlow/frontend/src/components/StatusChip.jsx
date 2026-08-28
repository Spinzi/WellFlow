/**
 * @param {{tone: "success"|"warning"|"error"|"neutral", label: string, pulse?: boolean}} props
 */
export default function StatusChip({ tone = "neutral", label, pulse = false }) {
  return (
    <span className={`chip chip--${tone} ${pulse ? "chip--pulse" : ""}`}>
      <span className="chip__dot" />
      {label}
    </span>
  );
}
