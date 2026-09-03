import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Two roles only: 'inspector' (can scan, view own history) and
    'admin' (can also view every inspector's history). Matches the brief's
    'role-based user access' requirement without overbuilding."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="inspector")  # "inspector" | "admin"
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanRecord(Base):
    """One row per inspection — the 'repository of scanned products and
    compliance history' required by the brief. Stores the evidence photo
    (base64) so it can be attached to the PDF report and reviewed later."""

    __tablename__ = "scan_records"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspector_username = Column(String, index=True, nullable=False)
    product_name = Column(String, default="Untitled product")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    verdict = Column(String, nullable=False)  # "pass" | "warn" | "fail"
    field_results = Column(JSON, nullable=False)       # list[dict] — declaration checklist
    ingredient_flags = Column(JSON, nullable=False)     # list[dict] — flagged ingredients
    raw_ocr_text = Column(Text, nullable=True)

    evidence_image_b64 = Column(Text, nullable=True)   # full-resolution photo, base64 JPEG
    annotated_image_b64 = Column(Text, nullable=True)  # photo with detection boxes drawn
