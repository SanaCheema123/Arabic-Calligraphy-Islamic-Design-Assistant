"""Application configuration (paths, defaults, feature flags)."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # app/
BACKEND_DIR = BASE_DIR.parent                       # backend/
PROJECT_DIR = BACKEND_DIR.parent                    # mishkat/

FONT_DIR = BASE_DIR / "fonts"
DATA_DIR = BACKEND_DIR / "data"
COMPOSITIONS_DIR = DATA_DIR / "compositions"
EXPORTS_DIR = DATA_DIR / "exports"

for _d in (FONT_DIR, DATA_DIR, COMPOSITIONS_DIR, EXPORTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Optional OCR validation; disabled gracefully when Tesseract is missing.
TESSERACT_LANG = os.environ.get("MISHKAT_TESS_LANG", "ara")
OCR_ENABLED = os.environ.get("MISHKAT_OCR", "1") == "1"

MAX_TEXT_CHARS = 120
MAX_EXPORT_DIMENSION = 8192
