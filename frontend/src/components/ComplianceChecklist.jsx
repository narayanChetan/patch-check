const DOT = { pass: { cls: "dot-pass", char: "✓" }, warn: { cls: "dot-warn", char: "!" }, fail: { cls: "dot-fail", char: "✕" } };

export default function ComplianceChecklist({ results }) {
  if (!results?.length) {
    return (
      <ul className="checklist">
        <li className="check-row">
          <div className="check-body">
            <p>Run a scan to see the declaration-by-declaration result here.</p>
          </div>
        </li>
      </ul>
    );
  }
  return (
    <ul className="checklist">
      {results.map((r) => {
        const dot = DOT[r.status] || DOT.warn;
        return (
          <li className="check-row" key={r.key}>
            <div className={`check-dot ${dot.cls}`}>{dot.char}</div>
            <div className="check-body">
              <b>{r.label}</b>
              <span className="rule">{r.rule}</span>
              <p>{r.note}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
