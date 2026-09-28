"""Offline smoke test: shape, render, pattern, validation, store, PNG raster."""
from __future__ import annotations

import sys

sys.path.insert(0, ".")

from app.arabic import shape, validate_text, normalize  # noqa: E402
from app.rendering.svgtext import render_text_svg, measure  # noqa: E402
from app.rendering.png import svg_to_png_safe  # noqa: E402
from app.rendering.composition import render_composition_svg  # noqa: E402
from app.patterns.generator import PatternParams, render_pattern_svg  # noqa: E402
from app.validation.ocr import accuracy_report, ocr_available  # OCR not needed
from app import store  # noqa: E402

TEXT = "العلم نور"


def main() -> int:
    ok = True

    # 1. shaping
    s = shape(TEXT)
    print("shaped:", s)
    assert s and s != TEXT, "shaping failed"

    # 2. text svg + measure
    svg = render_text_svg(TEXT, "naskh", 120)
    assert "<svg" in svg and "tspan" in svg, "text svg failed"
    w = measure(TEXT, "naskh", 120)
    print(f"measured width: {w:.0f}px")
    assert w > 50, "measure too small"

    # 3. pattern svg
    psvg = render_pattern_svg(PatternParams(style="khatam8", seed=3))
    assert "<svg" in psvg and "patternUnits" in psvg, "pattern svg failed"

    # 4. composition
    csvg = render_composition_svg(
        TEXT, "diwani_like", 140, pattern=PatternParams(style="girih10", seed=9),
    )
    assert "<svg" in csvg and "mk-comp-tile" in csvg, "composition svg failed"

    # 5. PNG rasterization (cairo)
    png, err = svg_to_png_safe(csvg, scale=1.0)
    assert not err and png.startswith(b"\x89PNG"), f"png failed: {err}"
    print(f"png bytes: {len(png)}")

    # 6. store round-trip
    doc = store.create({"params": {"text": TEXT, "style": "naskh", "font_size": 120,
                                   "text_fill": "#111", "background": "#f7f3e8",
                                   "width": 1200, "height": 1600}})
    doc2 = store.get(doc["id"])
    assert doc2 and doc2["id"] == doc["id"] and doc2["status"] == "draft"
    upd = store.update(doc["id"], status="pending_review")
    assert upd["status"] == "pending_review"
    rev = store.update(doc["id"], review={"decision": "approved", "reviewer": "t"},
                       status="approved")
    assert rev["status"] == "approved"
    lst = store.list_all("approved")
    assert any(d["id"] == doc["id"] for d in lst)
    assert store.delete(doc["id"]), "delete failed"

    # 7. validation report (OCR layer skipped if tesseract missing)
    rep = accuracy_report(TEXT, None)
    print("validation:", rep.to_dict())
    assert rep.passed, "validation should pass on clean text"

    print("OCR available:", ocr_available())
    print("ALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
