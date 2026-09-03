import { useEffect, useState } from "react";
import { api } from "../api/client";
import Navbar from "../components/Navbar";
import { useToast } from "../components/Toast";

const VERDICT_LABEL = { pass: "Compliant", warn: "Review", fail: "Non-compliant" };

export default function LedgerPage() {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [query, setQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const { toast, ToastEl } = useToast();

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function load(params = {}) {
    setLoading(true);
    try {
      const [ledgerData, statsData] = await Promise.all([api.listLedger(params), api.getStats()]);
      setEntries(ledgerData);
      setStats(statsData);
    } catch {
      toast("Could not load the ledger — try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    const params = {};
    if (query) params.q = query;
    if (verdictFilter) params.verdict = verdictFilter;
    load(params);
  }

  async function handleDeleteEntry(id) {
    try {
      await api.deleteScan(id);
      toast("Entry deleted.");
      load(query ? { q: query } : {});
    } catch {
      toast("Could not delete entry.");
    }
  }

  async function handleDownload(id) {
    try {
      const blob = await api.downloadReport(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `PackCheck_Report_${id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast("Could not download report.");
    }
  }

  return (
    <div className="app-shell">
      <Navbar />
      <section className="panel">
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: 18, margin: "0 0 14px" }}>
          Inspection ledger
        </h2>

        {stats && (
          <div className="stats-row">
            <div className="stat-card">
              <div className="num">{stats.total_scans}</div>
              <div className="lbl">Total scans</div>
            </div>
            <div className="stat-card">
              <div className="num">{stats.compliance_rate_pct ?? "—"}%</div>
              <div className="lbl">Compliance rate</div>
            </div>
            <div className="stat-card">
              <div className="num">{stats.by_verdict.fail}</div>
              <div className="lbl">Non-compliant</div>
            </div>
          </div>
        )}

        <form className="ledger-toolbar" onSubmit={handleSearch}>
          <input
            type="text" placeholder="Search by product or inspector…"
            value={query} onChange={(e) => setQuery(e.target.value)}
          />
          <select
            value={verdictFilter}
            onChange={(e) => setVerdictFilter(e.target.value)}
            style={{ padding: "10px 12px", borderRadius: 5, border: "1px solid rgba(20,35,28,0.22)" }}
          >
            <option value="">All verdicts</option>
            <option value="pass">Compliant</option>
            <option value="warn">Review required</option>
            <option value="fail">Non-compliant</option>
          </select>
          <button className="btn btn-outline" type="submit">Search</button>
        </form>

        {loading ? (
          <p className="ledger-empty">Loading ledger…</p>
        ) : entries.length === 0 ? (
          <p className="ledger-empty">No inspections logged yet — scan a label to see it here.</p>
        ) : (
          <div className="ledger-scroll">
            <table className="ledger">
              <thead>
                <tr>
                  <th>#</th><th>Scanned</th><th>Product</th><th>Inspector</th><th>Verdict</th><th>Flagged</th><th></th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e, i) => (
                  <tr key={e.id}>
                    <td style={{ fontFamily: "var(--font-mono)", color: "var(--brass)" }}>
                      {String(entries.length - i).padStart(3, "0")}
                    </td>
                    <td>{new Date(e.created_at).toLocaleString()}</td>
                    <td>{e.product_name}</td>
                    <td>{e.inspector_username}</td>
                    <td>
                      <span className={`badge badge-${e.verdict}`}>{VERDICT_LABEL[e.verdict] || e.verdict}</span>
                    </td>
                    <td>{e.flagged_field_count} field{e.flagged_field_count === 1 ? "" : "s"}{e.ingredient_flag_count ? `, ${e.ingredient_flag_count} ingredient` : ""}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button className="link-btn" onClick={() => handleDownload(e.id)}>PDF</button>
                      {"  "}
                      <button className="link-btn danger" onClick={() => handleDeleteEntry(e.id)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {ToastEl}
    </div>
  );
}
