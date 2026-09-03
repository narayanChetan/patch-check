"""
Screens OCR text for ingredients with documented FSSAI restrictions or
recognized health concerns (data/harmful_ingredients.json).

Honest limitation: Indian ingredient lists are ordered by descending
proportion, not labelled with exact quantities (except a few additives
that must state a class name/INS number). So "quantity" here is only ever
a best-effort read of a nearby percentage or mg figure — when none is
found, we say so explicitly rather than fabricating a number.
"""
import json
import re
from dataclasses import dataclass

from app.core.config import DATA_DIR

with open(DATA_DIR / "harmful_ingredients.json", encoding="utf-8") as f:
    INGREDIENT_DB = json.load(f)["ingredients"]

_QUANTITY_NEAR_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s?(%|mg|g|mg/kg|ppm)")


@dataclass
class IngredientFlag:
    id: str
    matched_text: str
    severity: str
    reason: str
    regulation: str
    quantity_hint: str | None = None


def _find_nearby_quantity(text_lower: str, match_start: int, match_end: int, window: int = 25) -> str | None:
    snippet = text_lower[max(0, match_start - window):min(len(text_lower), match_end + window)]
    m = _QUANTITY_NEAR_PATTERN.search(snippet)
    return m.group(0) if m else None


def screen_text(full_text: str) -> list[IngredientFlag]:
    text_lower = full_text.lower()
    flags: list[IngredientFlag] = []
    seen_ids = set()

    for entry in INGREDIENT_DB:
        if entry["id"] in seen_ids:
            continue
        for phrase in entry["match"]:
            m = re.search(re.escape(phrase), text_lower)
            if m:
                qty = _find_nearby_quantity(text_lower, m.start(), m.end())
                flags.append(IngredientFlag(
                    id=entry["id"],
                    matched_text=phrase,
                    severity=entry["severity"],
                    reason=entry["reason"],
                    regulation=entry["regulation"],
                    quantity_hint=qty,
                ))
                seen_ids.add(entry["id"])
                break

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda fl: severity_rank.get(fl.severity, 3))
    return flags
