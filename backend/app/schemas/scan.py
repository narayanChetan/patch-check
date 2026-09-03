from typing import Optional

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class FieldResult(BaseModel):
    key: str
    label: str
    rule: str
    status: str  # "pass" | "warn" | "fail"
    note: str
    boxes: list[BoundingBox] = []


class IngredientFlag(BaseModel):
    id: str
    matched_text: str
    severity: str  # "low" | "medium" | "high"
    reason: str
    regulation: str
    quantity_hint: Optional[str] = None


class ScanResponse(BaseModel):
    id: str
    product_name: str
    verdict: str
    field_results: list[FieldResult]
    ingredient_flags: list[IngredientFlag]
    raw_text_preview: str
    annotated_image_b64: str
    created_at: str


class LedgerEntry(BaseModel):
    id: str
    inspector_username: str
    product_name: str
    verdict: str
    created_at: str
    flagged_field_count: int
    ingredient_flag_count: int
