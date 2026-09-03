const VERDICT_TEXT = {
  pass: "Compliant",
  warn: "Review required",
  fail: "Non-compliant",
};

export default function VerdictStamp({ verdict }) {
  if (!verdict) return null;
  return (
    <div className="stamp-zone">
      <div className={`stamp stamp-${verdict}`}>
        <span>{VERDICT_TEXT[verdict] || verdict}</span>
        <small>PACKCHECK · AUTOMATED</small>
      </div>
    </div>
  );
}
