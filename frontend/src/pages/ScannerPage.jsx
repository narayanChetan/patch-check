import { useRef, useState } from "react";
import { api } from "../api/client";
import CameraCapture from "../components/CameraCapture";
import ComplianceChecklist from "../components/ComplianceChecklist";
import IngredientFlags from "../components/IngredientFlags";
import Navbar from "../components/Navbar";
import { useToast } from "../components/Toast";
import VerdictStamp from "../components/VerdictStamp";

export default function ScannerPage() {
  const [source, setSource] = useState("upload"); // "upload" | "camera"
  const [productName, setProductName] = useState("");
  const [previewUrl, setPreviewUrl] = useState(null);
  const [file, setFile] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const fileInputRef = useRef(null);
  const { toast, ToastEl } = useToast();

  function playClickSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(950, ctx.currentTime);
      gain.gain.setValueAtTime(0.06, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.045);
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.045);
    } catch {
      // Web Audio unavailable — non-critical, skip silently.
    }
  }

  function handleFileChosen(chosenFile) {
    setFile(chosenFile);
    setResult(null);
    setErrorMsg(null);
    const url = URL.createObjectURL(chosenFile);
    setPreviewUrl(url);
  }

  function onFileInputChange(e) {
    const f = e.target.files?.[0];
    if (f) handleFileChosen(f);
  }

  function onDrop(e) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) handleFileChosen(f);
  }

  async function runScan(scanFile) {
    setScanning(true);
    setErrorMsg(null);
    try {
      const data = await api.scanLabel(scanFile, productName, true);
      setResult(data);
      toast("Scan complete.");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Scan failed — try a clearer, well-lit photo.";
      setErrorMsg(msg);
    } finally {
      setScanning(false);
    }
  }

  function handleScanClick() {
    if (!file) return;
    runScan(file);
  }

  function handleCameraCapture(blob) {
    handleFileChosen(blob);
    runScan(blob);
  }

  async function handleDownloadPdf() {
    if (!result?.id || result.id === "unsaved") return;
    try {
      const blob = await api.downloadReport(result.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `PackCheck_Report_${result.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast("Could not download the report — try again.");
    }
  }

  return (
    <div className="app-shell">
      <Navbar />
      <section className="panel">
        <div className="scan-grid">
          <div>
            <label className="field-label" htmlFor="productName">Product name (optional)</label>
            <input
              id="productName" type="text" value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="e.g. Sunrise Refined Sunflower Oil, 1L"
            />
            <div style={{ height: 12 }} />

            <div className="source-toggle">
              <button
                type="button"
                className={`src-btn ${source === "upload" ? "active" : ""}`}
                onClick={() => { playClickSound(); setSource("upload"); }}
              >
                Upload photo
              </button>
              <button
                type="button"
                className={`src-btn ${source === "camera" ? "active" : ""}`}
                onClick={() => { playClickSound(); setSource("camera"); }}
              >
                Scan with camera
              </button>
            </div>

            {source === "upload" && (
              <>
                <label
                  className="dropzone"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={onDrop}
                  htmlFor="fileInput"
                >
                  <div style={{ fontSize: 26 }}>⤒</div>
                  <p><b>Click to upload</b> or drag a label photo here</p>
                  <p>JPG or PNG · a clear, well-lit photo works best</p>
                </label>
                <input
                  id="fileInput" ref={fileInputRef} type="file" accept="image/*"
                  onChange={onFileInputChange} style={{ display: "none" }}
                />
              </>
            )}

            {source === "camera" && <CameraCapture onCapture={handleCameraCapture} />}

            <div className="canvas-wrap" style={{ marginTop: 10 }}>
              {previewUrl ? (
                <img src={previewUrl} alt="Label preview" />
              ) : (
                <div className="canvas-empty">No label loaded yet.<br />Upload or capture a photo to begin an inspection.</div>
              )}
            </div>

            {source === "upload" && (
              <div className="btn-row">
                <button className="btn btn-primary" onClick={handleScanClick} disabled={!file || scanning}>
                  {scanning ? "Scanning…" : "Scan label"}
                </button>
              </div>
            )}
            {errorMsg && <p className="error-text">{errorMsg}</p>}
          </div>

          <div>
            <VerdictStamp verdict={result?.verdict} />
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: 16, margin: "0 0 8px" }}>
              Declaration checklist
            </h2>
            <ComplianceChecklist results={result?.field_results} />

            {result && (
              <div className="btn-row">
                <button className="btn btn-outline" onClick={handleDownloadPdf}>Download PDF report</button>
              </div>
            )}

            <IngredientFlags flags={result?.ingredient_flags} />

            <div className="disclaimer">
              <b>Prototype note —</b> font-size checks are estimated from the photo's pixel proportions
              (no physical reference is captured) and rule citations are indicative. Ingredient flags are
              informational, based on FSSAI regulations and published health guidance, not a certified lab
              assay. Always confirm findings against the official Legal Metrology (Packaged Commodities)
              Rules, 2011 before enforcement action.
            </div>
          </div>
        </div>
      </section>
      {ToastEl}
    </div>
  );
}
