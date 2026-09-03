"""
Central configuration for PackCheck.

All values can be overridden with environment variables of the same name
(see .env.example). Nothing here should contain real secrets — the defaults
are safe for local development only.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# --- Auth ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'packcheck.db'}")

# --- OCR / image processing ---
# Words with confidence below this (Tesseract's 0-100 scale) are discarded
# before rule-matching, to reduce false "detected" hits from noise.
MIN_OCR_CONFIDENCE = int(os.getenv("MIN_OCR_CONFIDENCE", "35"))

# Font-height heuristic fallback ratio (used only if the product's net
# quantity — and therefore the real Rule 7 mm threshold — can't be parsed).
FALLBACK_FONT_RATIO_WARN = 0.014

# --- CORS ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
