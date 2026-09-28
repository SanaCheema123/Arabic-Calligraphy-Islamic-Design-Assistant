"""Text-accuracy validation.

Two layers:
1. Structural checks (always available): character inventory, diacritics,
   length, mixed-direction risks.
2. OCR round-trip (optional, needs Tesseract with Arabic language data):
   rasterize the rendered SVG and read it back, then compare the OCR result
   with the requested text. Catches shaping/rendering mistakes (broken
   ligatures, disconnected letters, wrong glyph order).

The OCR layer is an assist, not a guarantee: final sign-off is the human
reviewer (see the review workflow in the API).
"""
from __future__ import annotations

import difflib
import io
import shutil
from dataclasses import dataclass, field

from ..arabic import validate_text, normalize, TextIssue
from ..config import OCR_ENABLED, TESSERACT_LANG


def ocr_available() -> bool:
    return bool(shutil.which("tesseract"))


@dataclass
class AccuracyReport:
    ocr_used: bool = False
    ocr_text: str = ""
    similarity: float = 0.0
    passed: bool = True
    issues: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ocr_used": self.ocr_used,
            "ocr_text": self.ocr_text,
            "similarity": round(self.similarity, 4),
            "passed": self.passed,
            "issues": self.issues,
        }


def structural_report(text: str, max_chars: int = 120) -> list[dict]:
    return [
        {"code": i.code, "message": i.message, "severity": i.severity}
        for i in validate_text(text, max_chars)
    ]


def ocr_png(png_bytes: bytes, lang: str = TESSERACT_LANG) -> str:
    import pytesseract
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes))
    return pytesseract.image_to_string(img, lang=lang).strip()


def accuracy_report(
    text: str,
    png_bytes: bytes | None = None,
    similarity_threshold: float = 0.85,
) -> AccuracyReport:
    """Full validation. If png_bytes is provided and Tesseract exists, OCR runs."""
    issues = structural_report(text)
    has_error = any(i["severity"] == "error" for i in issues)
    rep = AccuracyReport(ocr_used=False)
    rep.issues = issues

    if png_bytes and OCR_ENABLED and ocr_available():
        try:
            ocr_text = ocr_png(png_bytes)
            rep.ocr_used = True
            rep.ocr_text = ocr_text
            a = normalize(text)
            b = normalize(ocr_text)
            if a:
                rep.similarity = difflib.SequenceMatcher(None, a, b).ratio()
            if rep.similarity < similarity_threshold:
                rep.issues.append({
                    "code": "ocr_mismatch",
                    "message": (
                        f"OCR read-back similarity {rep.similarity:.2f} is below "
                        f"{similarity_threshold:.2f}. Check shaping/ligatures."
                    ),
                    "severity": "warning",
                })
        except Exception as exc:
            rep.issues.append({
                "code": "ocr_failed",
                "message": f"OCR step failed: {exc}",
                "severity": "info",
            })

    rep.passed = not has_error and not any(
        i["severity"] == "error" for i in rep.issues
    )
    return rep
