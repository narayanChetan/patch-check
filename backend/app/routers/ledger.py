from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import ScanRecord, User
from app.schemas.scan import LedgerEntry

router = APIRouter(prefix="/api/ledger", tags=["ledger"])


@router.get("", response_model=list[LedgerEntry])
def list_scans(
    q: Optional[str] = Query(None, description="Search by product name or inspector"),
    verdict: Optional[str] = Query(None, description="Filter: pass | warn | fail"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Inspectors see only their own scans; admins see everyone's —
    the 'role-based access' + 'search and retrieval' requirements from the
    brief, combined into one endpoint."""
    query = db.query(ScanRecord)
    if user.role != "admin":
        query = query.filter(ScanRecord.inspector_username == user.username)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(ScanRecord.product_name.ilike(like), ScanRecord.inspector_username.ilike(like)))
    if verdict:
        query = query.filter(ScanRecord.verdict == verdict)

    records = query.order_by(ScanRecord.created_at.desc()).limit(200).all()
    return [
        LedgerEntry(
            id=r.id,
            inspector_username=r.inspector_username,
            product_name=r.product_name,
            verdict=r.verdict,
            created_at=r.created_at.isoformat(),
            flagged_field_count=sum(1 for fr in r.field_results if fr["status"] != "pass"),
            ingredient_flag_count=len(r.ingredient_flags),
        )
        for r in records
    ]


@router.get("/{scan_id}")
def get_scan_detail(scan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()
    if not record:
        raise HTTPException(404, "Scan not found.")
    if user.role != "admin" and record.inspector_username != user.username:
        raise HTTPException(403, "You can only view your own scans.")
    return {
        "id": record.id,
        "inspector_username": record.inspector_username,
        "product_name": record.product_name,
        "verdict": record.verdict,
        "created_at": record.created_at.isoformat(),
        "field_results": record.field_results,
        "ingredient_flags": record.ingredient_flags,
        "annotated_image_b64": record.annotated_image_b64,
    }


@router.delete("/{scan_id}")
def delete_scan(scan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()
    if not record:
        raise HTTPException(404, "Scan not found.")
    if user.role != "admin" and record.inspector_username != user.username:
        raise HTTPException(403, "You can only delete your own scans.")
    db.delete(record)
    db.commit()
    return {"deleted": True}


@router.get("/stats/summary")
def summary_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Aggregate numbers for the dashboard view (compliance rate, totals,
    top violated fields) — the 'dashboard for enforcement officials'
    requirement, beyond just a flat list."""
    query = db.query(ScanRecord)
    if user.role != "admin":
        query = query.filter(ScanRecord.inspector_username == user.username)
    records = query.all()

    total = len(records)
    by_verdict = {"pass": 0, "warn": 0, "fail": 0}
    violation_counts: dict[str, int] = {}
    for r in records:
        by_verdict[r.verdict] = by_verdict.get(r.verdict, 0) + 1
        for fr in r.field_results:
            if fr["status"] != "pass":
                violation_counts[fr["label"]] = violation_counts.get(fr["label"], 0) + 1

    top_violations = sorted(violation_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
    compliance_rate = round(100 * by_verdict["pass"] / total, 1) if total else None

    return {
        "total_scans": total,
        "by_verdict": by_verdict,
        "compliance_rate_pct": compliance_rate,
        "top_violations": [{"label": label, "count": count} for label, count in top_violations],
    }
