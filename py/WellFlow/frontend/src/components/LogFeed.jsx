function formatTime(ts) {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function LogFeed({ entries }) {
  if (!entries || entries.length === 0) {
    return <p className="log-feed__empty">No messages yet.</p>;
  }

  return (
    <div className="log-feed">
      {entries.map((entry, i) => (
        <div className="log-entry" key={`${entry.ts}-${i}`}>
          <span className={`log-entry__dot log-entry__dot--${entry.kind}`} />
          <span>
            <span className="log-entry__text">{entry.text}</span>
            <span className="log-entry__time">{formatTime(entry.ts)}</span>
          </span>
        </div>
      ))}
    </div>
  );
}
