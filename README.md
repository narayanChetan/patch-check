# PackCheck

**Legal Metrology (Packaged Commodities) Rules, 2011 — compliance scanner**
Smart India Hackathon 2026 · Problem Statement **SIH26034** · Ministry of Consumer Affairs, Food & Public Distribution

PackCheck lets an inspector (or eventually a shopper) photograph a packaged product's label and get an instant, evidence-backed compliance verdict — which mandatory declarations are present, which are missing, which are too small to legally read, and which ingredients carry an FSSAI restriction or health warning.

---

## Architecture

```
packcheck/
├── backend/          FastAPI + OpenCV + Tesseract OCR + SQLite
│   └── app/
│       ├── core/         config, JWT auth, security
│       ├── db/           SQLAlchemy models (users, scan records)
│       ├── schemas/      Pydantic request/response models
│       ├── services/     preprocessing, OCR, rule engine, ingredient
│       │                 screener, report generator, annotation
│       ├── routers/      auth, scan, ledger API endpoints
│       └── data/         legal_metrology_fields.json,
│                         harmful_ingredients.json  (the actual rule data)
│   └── tests/            pytest suite (unit + API integration)
└── frontend/         React (Vite) — mobile-first, camera capture
    └── src/
        ├── api/, context/, pages/, components/, styles/
```

**Why a real backend instead of a single HTML file:** OpenCV's deskew/denoise/contrast pipeline and Tesseract's LSTM engine are dramatically more accurate on real, imperfect phone photos than the browser-based `tesseract.js` port used in the first prototype iteration — that's what was silently missing a visible MRP on a real photo. This version fixes that class of bug at the root.

### Pipeline (what happens on one scan)

1. **Preprocess** (`services/preprocessing.py`) — upscale small photos, grayscale, deskew via minimum-area-rectangle rotation correction, denoise, CLAHE contrast enhancement, adaptive threshold.
2. **OCR** (`services/ocr_engine.py`) — real Tesseract (`pytesseract`, PSM 6, OEM 3/LSTM) returns word-level text, confidence, and pixel bounding boxes.
3. **Rule engine** (`services/rule_engine.py`) — matches OCR text against fields defined in `data/legal_metrology_fields.json`, which was built directly from the official Rule 6(1)(a)-(g), Rule 6(2), Rule 7 (font-size table), and Rule 9 (language/contrast) text — not guessed.
4. **Ingredient screener** (`services/ingredient_screener.py`) — flags ingredients in `data/harmful_ingredients.json` (potassium bromate, trans fats, MSG, artificial sweeteners/colours, sodium benzoate, sodium nitrite, etc.), each with a real FSSAI regulation citation.
5. **Annotation + report** — detection boxes drawn on the photo, PDF report generated with `reportlab`, everything persisted to SQLite (`ScanRecord`) as the inspection ledger.

---

## Running it

### Option A — Docker (simplest)
```bash
docker compose up --build
```
Frontend: http://localhost:5173 · Backend: http://localhost:8000/docs

### Option B — manual

**Backend:**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Tesseract must be installed on the system:
#   Ubuntu/Debian: sudo apt-get install tesseract-ocr
#   macOS:         brew install tesseract
cp .env.example .env   # edit JWT_SECRET_KEY before any real deployment
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_URL if backend isn't on localhost:8000
npm run dev
```

Open the printed `http://localhost:5173` URL **in a real browser tab** — camera capture requires HTTPS or `localhost`; it will not work if the page is opened via `file://` or inside a sandboxed preview frame.

### Demo accounts (seeded automatically, change before real use)
| Username | Password | Role |
|---|---|---|
| `inspector` | `inspector123` | inspector — sees only their own scans |
| `admin` | `admin123` | admin — sees every inspector's scans + stats |

---

## Testing

```bash
cd backend
pytest tests/ -v
```

18 tests covering:
- **Rule engine** — a real MRP on a synthetic label is detected (regression test for the reported bug); a label missing MRP correctly fails; an MRP without the mandatory "inclusive of all taxes" phrase correctly warns (Rule 2(m)); every field definition carries a genuine rule citation.
- **Ingredient screener** — banned/restricted additives are flagged with correct severity ordering; clean ingredient lists produce zero false positives; nearby quantity figures are picked up when present.
- **API integration** — auth, full scan→PDF flow, role-based access (an inspector cannot see another inspector's scans; only admins can), search, delete.

Test images are generated synthetically at test time (`tests/conftest.py`) with realistic imperfections (rotation, noise) — no external image files are committed to the repo.

---

## What's real vs. what's a heuristic (read this before a demo)

Being upfront about this protects you from over-claiming in front of judges:

- **Rule citations** (Rule 6(1)(a)-(g), Rule 7, Rule 9) are drawn from the actual gazette text of the Legal Metrology (Packaged Commodities) Rules, 2011 — not invented.
- **Font-size compliance** is estimated from the photo's own pixel proportions using an assumed DPI, since no physical reference object is captured in the frame. Treat a "too small" warning as "worth checking with a ruler," not a certified measurement.
- **Ingredient flags** are informational, based on published FSSAI regulations and health guidance — this is not a certified lab assay, and "quantity" is only ever a best-effort read of a nearby percentage/mg figure, since Indian ingredient lists are ordered by proportion, not exact quantity (except for a few specifically mandated additives).
- **The "AI" here is a deterministic OCR + rule-matching pipeline, not a trained model.** No custom neural network was trained for this — there is no public labeled dataset of Indian product labels to train one, and building one is a separate, much larger project. What was upgraded is the OCR engine and preprocessing, which is the highest-leverage fix for real-photo accuracy.

## Known gaps / good next steps
- Country-of-origin and generic-name checks are weaker than the core five fields — they're harder to verify without a product taxonomy.
- No multi-language (Hindi/Devanagari) OCR yet — Rule 9(4) permits Hindi labels, and `pytesseract` supports it (`lang="eng+hin"`), but the `hin` trained-data file isn't bundled here.
- No automated retraining loop — if you get access to real annotated label photos, the highest-value next step is fine-tuning field-detection thresholds against that real data, not building a new model from scratch.
