from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import ScanRecord, User
from app.schemas.scan import ScanResponse
from app.services import ingredient_screener, ocr_engine, preprocessing, rule_engine
from app.services.annotate import draw_detection_boxes, image_to_b64_jpeg
from app.services.report_generator import build_pdf_report

router = APIRouter(prefix="/api/scan", tags=["scan"])

MAX_UPLOAD_BYTES = 12 * 1024 * 1024  # 12 MB


def _decode_upload(raw: bytes) -> np.ndarray:
    arr = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(400, "Could not read that image — try a different photo.")
    return image


@router.post("", response_model=ScanResponse)
async def scan_label(
    file: UploadFile = File(...),
    product_name: str = Form("Untitled product"),
    save: bool = Form(True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Please upload an image file.")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "Image is too large (max 12 MB).")

    image_bgr = _decode_upload(raw)
    display_bgr, ocr_ready_gray = preprocessing.preprocess_for_ocr(image_bgr)

    ocr_result = ocr_engine.run_ocr(ocr_ready_gray)
    outcomes = rule_engine.evaluate(ocr_result)
    verdict = rule_engine.compute_verdict(outcomes)
    ingredient_flags = ingredient_screener.screen_text(ocr_result.full_text)

    annotated_bgr = draw_detection_boxes(display_bgr, outcomes)
    annotated_b64 = image_to_b64_jpeg(annotated_bgr)
    evidence_b64 = image_to_b64_jpeg(display_bgr)

    field_results_json = [
        {
            "key": o.key, "label": o.label, "rule": o.rule, "status": o.status, "note": o.note,
            "boxes": [{"x0": b.x0, "y0": b.y0, "x1": b.x1, "y1": b.y1} for b in o.boxes],
        }
        for o in outcomes
    ]
    ingredient_flags_json = [
        {
            "id": fl.id, "matched_text": fl.matched_text, "severity": fl.severity,
            "reason": fl.reason, "regulation": fl.regulation, "quantity_hint": fl.quantity_hint,
        }
        for fl in ingredient_flags
    ]

    created_at = datetime.now(timezone.utc).isoformat()
    record = ScanRecord(
        inspector_username=user.username,
        product_name=product_name or "Untitled product",
        created_at=datetime.now(timezone.utc),
        verdict=verdict,
        field_results=field_results_json,
        ingredient_flags=ingredient_flags_json,
        raw_ocr_text=ocr_result.full_text,
        evidence_image_b64=evidence_b64,
        annotated_image_b64=annotated_b64,
    )
    if save:
        db.add(record)
        db.commit()
        db.refresh(record)
    else:
        record.id = "unsaved"

    return ScanResponse(
        id=record.id,
        product_name=record.product_name,
        verdict=verdict,
        field_results=field_results_json,
        ingredient_flags=ingredient_flags_json,
        raw_text_preview=ocr_result.full_text[:400],
        annotated_image_b64=annotated_b64,
        created_at=created_at,
    )


@router.get("/{scan_id}/report.pdf")
def download_report(scan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()
    if not record:
        raise HTTPException(404, "Scan not found.")
    if user.role != "admin" and record.inspector_username != user.username:
        raise HTTPException(403, "You can only download your own scan reports.")

    pdf_bytes = build_pdf_report(
        product_name=record.product_name,
        verdict=record.verdict,
        field_results=record.field_results,
        ingredient_flags=record.ingredient_flags,
        annotated_image_b64=record.annotated_image_b64,
        created_at=record.created_at.isoformat(),
    )
    filename = f"PackCheck_Report_{scan_id}.pdf"
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
