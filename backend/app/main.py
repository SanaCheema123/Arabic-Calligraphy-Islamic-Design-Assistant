"""FastAPI application: composition, pattern, validation and export endpoints."""
from __future__ import annotations

import base64
import io
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .config import EXPORTS_DIR, MAX_EXPORT_DIMENSION, MAX_TEXT_CHARS
from .arabic import validate_text
from .rendering.svgtext import STYLES, DEFAULT_STYLE, render_text_svg
from .rendering.png import svg_to_png_safe
from .rendering.composition import render_composition_svg
from .patterns.generator import PALETTES, PatternParams, render_pattern_svg, variants
from .validation.ocr import accuracy_report, ocr_available
from . import store

app = FastAPI(title="Mishkat API", version="0.1.0",
              description="Arabic calligraphy compositions & Saudi-inspired patterns.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- schemas ---

class PatternIn(BaseModel):
    style: str = "khatam8"
    seed: int = 7
    tile: int = Field(160, ge=40, le=640)
    cols: int = Field(4, ge=1, le=40)
    rows: int = Field(4, ge=1, le=40)
    palette: str = "sand"
    colors: list[str] | None = None
    line_width: float = Field(2.0, ge=0.2, le=12)
    background: str | None = None


class CompositionIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_CHARS)
    style: str = DEFAULT_STYLE
    font_size: float = Field(120, ge=16, le=480)
    text_fill: str = "#1c1c1c"
    background: str = "#f7f3e8"
    width: int = Field(1200, ge=200, le=MAX_EXPORT_DIMENSION)
    height: int = Field(1600, ge=200, le=MAX_EXPORT_DIMENSION)
    pattern: PatternIn | None = None
    pattern_opacity: float = Field(0.12, ge=0, le=1)
    text_position: str = "center"


class ReviewIn(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|changes_requested)$")
    reviewer: str = "anonymous"
    notes: str = ""


# ------------------------------------------------------------- utilities ---

def _pattern_from(p: PatternIn | None) -> PatternParams | None:
    if p is None:
        return None
    return PatternParams(
        style=p.style, seed=p.seed, tile=p.tile, cols=p.cols, rows=p.rows,
        palette=p.palette, colors=p.colors or [], line_width=p.line_width,
        background=p.background,
    )


def _composition_svg(doc: dict) -> str:
    p = doc["params"]
    return render_composition_svg(
        text=p["text"], style_key=p["style"], font_size=p["font_size"],
        text_fill=p["text_fill"], background=p["background"],
        width=p["width"], height=p["height"],
        pattern=_pattern_from(PatternIn(**(p.get("pattern") or {}))) if p.get("pattern") else None,
        pattern_opacity=p.get("pattern_opacity", 0.12),
        text_position=p.get("text_position", "center"),
    )


# --------------------------------------------------------------- meta ---

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "ocr_available": ocr_available(),
        "styles": [{"key": k, "label": v[1]} for k, v in STYLES.items()],
    }


@app.get("/api/meta")
def meta():
    return {
        "styles": [
            {"key": k, "label": STYLES[k][1], "font": STYLES[k][0]}
            for k in STYLES
        ],
        "palettes": PALETTES,
        "pattern_styles": ["khatam8", "girih10", "star12", "squares", "braid"],
        "ocr_available": ocr_available(),
        "max_text_chars": MAX_TEXT_CHARS,
    }


# ------------------------------------------------------- pattern engine ---

@app.post("/api/pattern")
def pattern_svg(p: PatternIn):
    if p.style not in ("khatam8", "girih10", "star12", "squares", "braid"):
        raise HTTPException(400, f"unknown style {p.style}")
    return Response(render_pattern_svg(_pattern_from(p)), media_type="image/svg+xml")


@app.post("/api/pattern/variants")
def pattern_variants(p: PatternIn, count: int = Query(6, ge=1, le=12)):
    if p.style not in ("khatam8", "girih10", "star12", "squares", "braid"):
        raise HTTPException(400, f"unknown style {p.style}")
    return {"variants": [
        {"seed": v["seed"], "svg": v["svg"]}
        for v in variants(_pattern_from(p), count)
    ]}


# ----------------------------------------------------- text-only render ---

@app.post("/api/render/text")
def render_text(p: CompositionIn):
    issues = validate_text(p.text, MAX_TEXT_CHARS)
    svg = render_text_svg(
        p.text, p.style, p.font_size, p.text_fill, p.background,
        max_width=p.width - 128,
    )
    return {"svg": svg, "issues": [i.__dict__ for i in issues]}


@app.post("/api/render/composition")
def render_composition_preview(p: CompositionIn):
    """Stateless preview: returns the composed SVG without persisting anything."""
    issues = validate_text(p.text, MAX_TEXT_CHARS)
    svg = render_composition_svg(
        text=p.text, style_key=p.style, font_size=p.font_size,
        text_fill=p.text_fill, background=p.background,
        width=p.width, height=p.height,
        pattern=_pattern_from(p.pattern),
        pattern_opacity=p.pattern_opacity,
        text_position=p.text_position,
    )
    return {"svg": svg, "issues": [i.__dict__ for i in issues]}


# -------------------------------------------------------- compositions ---

@app.post("/api/compositions")
def create_composition(p: CompositionIn):
    if p.style not in STYLES:
        raise HTTPException(400, f"unknown style {p.style}")
    doc = store.create({"params": p.model_dump()})
    doc["svg"] = _composition_svg(doc)
    return doc


@app.get("/api/compositions")
def list_compositions(status: str | None = None):
    return {"items": store.list_all(status)}


@app.get("/api/compositions/{cid}")
def get_composition(cid: str):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    return {**doc, "svg": doc.get("svg") or _composition_svg(doc)}


@app.get("/api/compositions/{cid}/svg")
def composition_svg(cid: str):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    svg = doc.get("svg") or _composition_svg(doc)
    return Response(svg, media_type="image/svg+xml")


@app.put("/api/compositions/{cid}")
def update_composition(cid: str, p: CompositionIn):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    if doc["status"] not in ("draft", "changes_requested"):
        raise HTTPException(409, f"cannot edit a composition in status '{doc['status']}'")
    updated = store.update(cid, params=p.model_dump())
    updated["svg"] = _composition_svg(updated)
    return updated


@app.delete("/api/compositions/{cid}")
def delete_composition(cid: str):
    if not store.delete(cid):
        raise HTTPException(404, "not found")
    return {"ok": True}


# ---------------------------------------------------------- validation ---

@app.post("/api/compositions/{cid}/validate")
def validate_composition(cid: str):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    svg = doc.get("svg") or _composition_svg(doc)
    png, err = svg_to_png_safe(svg, scale=1.0, dpi=150)
    rep = accuracy_report(doc["params"]["text"], png if not err else None)
    return rep.to_dict()


@app.post("/api/validate/text")
def validate_text_endpoint(p: CompositionIn):
    issues = validate_text(p.text, MAX_TEXT_CHARS)
    png, err = svg_to_png_safe(render_text_svg(p.text, p.style, p.font_size), scale=1.0)
    rep = accuracy_report(p.text, png if not err else None)
    return rep.to_dict()


# ------------------------------------------------------------- review ---

@app.post("/api/compositions/{cid}/submit")
def submit_for_review(cid: str):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    if doc["status"] not in ("draft", "changes_requested"):
        raise HTTPException(409, f"cannot submit from status '{doc['status']}'")
    return store.update(cid, status="pending_review")


@app.get("/api/review/queue")
def review_queue():
    return {"items": store.list_all("pending_review")}


@app.post("/api/compositions/{cid}/review")
def review_composition(cid: str, r: ReviewIn):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    if doc["status"] != "pending_review":
        raise HTTPException(409, "composition is not awaiting review")
    return store.update(
        cid,
        status=r.decision if r.decision != "changes_requested" else "changes_requested",
        review={"decision": r.decision, "reviewer": r.reviewer, "notes": r.notes},
    )


# ------------------------------------------------------------- export ---

@app.api_route("/api/compositions/{cid}/export", methods=["GET", "POST"])
def export_composition(cid: str, scale: float = Query(2.0, ge=0.5, le=8)):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    if doc["status"] != "approved":
        raise HTTPException(403, "only approved compositions can be exported")
    svg = doc.get("svg") or _composition_svg(doc)
    png, err = svg_to_png_safe(svg, scale=scale, dpi=300)
    if err or not png:
        raise HTTPException(500, err or "export failed")
    token = uuid.uuid4().hex[:10]
    (EXPORTS_DIR / f"{doc['id']}-{token}.png").write_bytes(png)
    return Response(
        png,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="mishkat-{doc["id"]}.png"'},
    )


@app.get("/api/compositions/{cid}/export/svg")
def export_composition_svg(cid: str):
    doc = store.get(cid)
    if doc is None:
        raise HTTPException(404, "not found")
    if doc["status"] != "approved":
        raise HTTPException(403, "only approved compositions can be exported")
    svg = doc.get("svg") or _composition_svg(doc)
    return Response(
        svg,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'attachment; filename="mishkat-{cid}.svg"'},
    )
