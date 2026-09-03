"""
Rule engine for the Legal Metrology (Packaged Commodities) Rules, 2011.

Field definitions and font-size thresholds are loaded from
data/legal_metrology_fields.json, which was built directly from the
official rules text (see the file's "_source" field) rather than guessed —
this is what makes the checklist's rule citations trustworthy rather than
decorative.
"""
import json
import re
from dataclasses import dataclass, field

from app.core.config import DATA_DIR, FALLBACK_FONT_RATIO_WARN
from app.services.ocr_engine import OcrResult, OcrWord

with open(DATA_DIR / "legal_metrology_fields.json", encoding="utf-8") as f:
    RULES = json.load(f)

FIELDS = RULES["fields"]
FONT_TABLE = RULES["font_size_table_mm"]["rows"]


def _phrase_to_regex(phrase: str) -> re.Pattern:
    """Converts a plain-English phrase like 'mfd by' into a regex that
    tolerates punctuation between words (periods, colons, extra spaces) —
    real labels print things as 'Mfd. by:' or 'Net Qty:-' constantly, and a
    literal substring match misses all of those."""
    tokens = phrase.split()
    pattern = r"\W*".join(re.escape(t) for t in tokens)
    return re.compile(pattern, re.IGNORECASE)


def _any_phrase_found(text_lower: str, phrases: list[str]) -> bool:
    return any(_phrase_to_regex(p).search(text_lower) for p in phrases)


@dataclass
class FieldOutcome:
    key: str
    label: str
    rule: str
    status: str  # "pass" | "warn" | "fail"
    note: str
    boxes: list[OcrWord] = field(default_factory=list)


def _min_font_mm_for_quantity(qty_value: float | None) -> float:
    """Rule 7, Table I: minimum numeral height depends on declared net
    quantity. Falls back to the strictest (smallest-pack) threshold if the
    quantity couldn't be parsed, which is the safer default for flagging."""
    if qty_value is None:
        return FONT_TABLE[0]["min_height_mm"]
    for row in FONT_TABLE:
        cap = row.get("max_net_quantity_g_or_ml")
        if cap is not None and qty_value <= cap:
            return row["min_height_mm"]
    return FONT_TABLE[-1]["min_height_mm"]


def _extract_net_quantity_value(text_lower: str) -> float | None:
    m = re.search(r"\b(\d+(?:\.\d+)?)\s?(g|gm|gms|kg|ml|l)\b", text_lower)
    if not m:
        return None
    value, unit = float(m.group(1)), m.group(2)
    if unit == "kg":
        value *= 1000
    if unit == "l":
        value *= 1000
    return value


def _words_matching_any(all_words: list[OcrWord], full_text_lower: str, phrases: list[str]) -> list[OcrWord]:
    """Finds which OCR words fall inside any occurrence of the given phrases
    in the concatenated lowercase text, so we can draw a box around them.

    IMPORTANT: `all_words` must be in the exact same order used to build
    `full_text_lower` (i.e. OcrResult.all_words + OcrResult.full_text), or
    the character offsets computed here will not line up with the regex
    match positions and matching will silently misfire.
    """
    matched: list[OcrWord] = []
    offsets = []
    cursor = 0
    for w in all_words:
        start = cursor
        end = start + len(w.text)
        offsets.append((start, end, w))
        cursor = end + 1  # +1 for the joining space

    for phrase in phrases:
        pattern = _phrase_to_regex(phrase)
        for m in pattern.finditer(full_text_lower):
            mstart, mend = m.start(), m.end()
            for start, end, w in offsets:
                if start < mend and end > mstart and w not in matched:
                    matched.append(w)
    return matched


def evaluate(ocr: OcrResult, dpi_estimate: float = 200.0) -> list[FieldOutcome]:
    """Runs every configured field check against the OCR output.

    dpi_estimate: pixels-per-inch used to convert a word's pixel height into
    millimetres for the Rule 7 font-size check. This is inherently a rough
    estimate from a phone photo (no physical reference is captured), so the
    font-size verdict is always reported as a heuristic — see the "note".
    """
    full_text_lower = ocr.full_text.lower()
    qty_value = _extract_net_quantity_value(full_text_lower)
    min_font_mm = _min_font_mm_for_quantity(qty_value)
    mm_per_pixel = 25.4 / dpi_estimate

    outcomes: list[FieldOutcome] = []

    for f in FIELDS:
        label_patterns = f.get("label_patterns")
        value_pattern = f.get("value_pattern")
        heuristic_only = f.get("heuristic_only", False)

        if heuristic_only:
            # Generic-name check: we can't reliably verify this without a
            # product taxonomy, so we report it as informational rather
            # than pass/fail to avoid a false sense of certainty.
            outcomes.append(FieldOutcome(
                key=f["key"], label=f["label"], rule=f["rule"], status="warn",
                note="Not automatically verifiable — confirm the product's common name is printed on the label.",
            ))
            continue

        label_found = False
        matched_words: list[OcrWord] = []
        if label_patterns:
            label_found = _any_phrase_found(full_text_lower, label_patterns)
            if label_found:
                raw_matches = _words_matching_any(ocr.all_words, full_text_lower, label_patterns)
                # Only trust confidence-filtered words for drawing/measurement;
                # the label text itself was still found via full_text search above.
                trusted_ids = {id(w) for w in ocr.words}
                matched_words = [w for w in raw_matches if id(w) in trusted_ids]
        else:
            # No fixed keyword (e.g. country of origin has synonyms already
            # in label_patterns; this branch is currently unused but kept
            # for fields that may only need a value_pattern in future).
            label_found = False

        if not label_found:
            status = "fail" if f["required"] else "warn"
            note = (
                "No declaration found on the label for this requirement."
                if f["required"] else
                "Not found — only required for imported packages / specific commodity types."
            )
            outcomes.append(FieldOutcome(key=f["key"], label=f["label"], rule=f["rule"], status=status, note=note))
            continue

        if value_pattern and not re.search(value_pattern, full_text_lower):
            outcomes.append(FieldOutcome(
                key=f["key"], label=f["label"], rule=f["rule"], status="warn",
                note="Heading detected, but the expected value format wasn't confidently read nearby.",
                boxes=matched_words,
            ))
            continue

        if f["key"] == "mrp" and f.get("requires_inclusive_phrase"):
            if not re.search(r"incl|inclusive", full_text_lower):
                outcomes.append(FieldOutcome(
                    key=f["key"], label=f["label"], rule=f["rule"], status="warn",
                    note="MRP found, but the mandatory 'inclusive of all taxes' qualifier wasn't detected (Rule 2(m)).",
                    boxes=matched_words,
                ))
                continue

        # Font-size check for the two fields Rule 7 actually regulates.
        if f["key"] in ("mrp", "net_quantity") and matched_words:
            avg_height_px = sum(w.y1 - w.y0 for w in matched_words) / len(matched_words)
            height_mm = avg_height_px * mm_per_pixel
            if height_mm < min_font_mm:
                outcomes.append(FieldOutcome(
                    key=f["key"], label=f["label"], rule=f["rule"], status="warn",
                    note=(
                        f"Declaration present, but estimated font height (~{height_mm:.1f} mm) is below the "
                        f"Rule 7 minimum of {min_font_mm} mm for this pack size. Estimate depends on photo "
                        f"resolution/distance — verify with a ruler before citing."
                    ),
                    boxes=matched_words,
                ))
                continue

        outcomes.append(FieldOutcome(
            key=f["key"], label=f["label"], rule=f["rule"], status="pass",
            note="Declaration found and appears complete.", boxes=matched_words,
        ))

    return outcomes


def compute_verdict(outcomes: list[FieldOutcome]) -> str:
    if any(o.status == "fail" for o in outcomes):
        return "fail"
    if any(o.status == "warn" for o in outcomes):
        return "warn"
    return "pass"
