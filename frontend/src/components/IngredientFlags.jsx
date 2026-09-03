export default function IngredientFlags({ flags }) {
  if (!flags?.length) return null;
  return (
    <div style={{ marginTop: 18 }}>
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: 16, margin: "0 0 10px" }}>
        Flagged ingredients ({flags.length})
      </h2>
      {flags.map((f) => (
        <div className={`ingredient-card sev-${f.severity}`} key={f.id}>
          <div className="ing-head">
            <b>{f.matched_text}</b>
            <span className="severity-tag">{f.severity}</span>
          </div>
          <p>{f.reason}</p>
          {f.quantity_hint && <p style={{ fontStyle: "italic" }}>Detected near: {f.quantity_hint}</p>}
          <div className="reg">{f.regulation}</div>
        </div>
      ))}
    </div>
  );
}
