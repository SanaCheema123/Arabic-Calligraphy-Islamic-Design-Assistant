"""Generative Islamic geometric patterns as standalone SVG.

Deterministic procedural generator: a small library of classical motifs drawn
with exact geometry:
  - 8-fold khatam star-and-rosette (Mamluk/Cordoba)
  - 10-fold girih rosette
  - 12-fold star grid
  - nested squares (muqarnas-inspired)
  - interlaced kufi braid

Every pattern can be tiled, recolored and re-seeded, so the frontend can
generate hundreds of variants deterministically from (style, seed, colors).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

TAU = 2 * math.pi

PALETTES: dict[str, list[str]] = {
    "sand":     ["#1c1c1c", "#c9a227", "#0f7173", "#f7f3e8"],
    "oasis":    ["#0b3d2e", "#1b998b", "#d9c58b", "#f4f1ea"],
    "night":    ["#0d1b2a", "#1b998b", "#e0c097", "#faf3e0"],
    "ryiad":    ["#153e90", "#c9a227", "#2e6f40", "#f6f2e7"],
    "monochrome": ["#111111", "#555555", "#999999", "#ffffff"],
}


@dataclass
class PatternParams:
    style: str = "khatam8"       # khatam8 | girih10 | star12 | squares | braid
    seed: int = 7
    tile: int = 160              # base tile size in px
    cols: int = 4
    rows: int = 4
    palette: str = "sand"
    colors: list[str] = field(default_factory=list)  # overrides palette
    line_width: float = 2.0
    background: str | None = None  # default: palette[3]

    def resolve_colors(self) -> list[str]:
        if self.colors and len(self.colors) >= 3:
            return self.colors[:4]
        return PALETTES.get(self.palette, PALETTES["sand"])


def _polygon(cx: float, cy: float, r: float, n: int, rotation: float = 0.0) -> str:
    pts = []
    for i in range(n):
        a = rotation + TAU * i / n
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return " ".join(pts)


def _star(cx: float, cy: float, r: float, points: int, inner_ratio: float, rotation: float = 0.0) -> str:
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * inner_ratio
        a = rotation + TAU * i / (points * 2)
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return " ".join(pts)


def _rosette_paths(cx: float, cy: float, r: float, fold: int, rotation: float = 0.0) -> list[str]:
    """Interlaced rosette: n/2 crossing chords through the fold points."""
    paths = []
    for i in range(fold):
        a1 = rotation + TAU * i / fold
        a2 = rotation + TAU * (i + fold // 2 - 1) / fold
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        paths.append(f"M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f}")
    return paths


def _tile_svg(p: PatternParams, rng: random.Random) -> str:
    """Draw one tile of the chosen motif centered at (tile/2, tile/2)."""
    t = p.tile
    c = p.resolve_colors()
    stroke, accent, secondary = c[0], c[1], c[2]
    cx = cy = t / 2
    r = t * 0.42
    lw = p.line_width
    parts: list[str] = []

    def poly(points: str, fill: str = "none", color: str = stroke, w: float | None = None) -> str:
        return (f'<polygon points="{points}" fill="{fill}" '
                f'stroke="{color}" stroke-width="{w if w is not None else lw}"/>')

    if p.style == "khatam8":
        # Two overlapping squares (45 degrees apart) = 8-point khatam.
        parts.append(poly(_polygon(cx, cy, r, 4, math.pi / 4)))
        parts.append(poly(_polygon(cx, cy, r, 4, 0.0)))
        parts.append(poly(_star(cx, cy, r * 0.55, 8, 0.45), fill=accent, color=stroke, w=lw * 0.6))
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.16:.2f}" fill="{secondary}"/>')
    elif p.style == "girih10":
        for d in _rosette_paths(cx, cy, r, 10):
            parts.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{lw}" fill="none"/>')
        parts.append(poly(_star(cx, cy, r * 0.62, 10, 0.55), fill="none", color=accent))
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.14:.2f}" fill="{secondary}"/>')
    elif p.style == "star12":
        parts.append(poly(_star(cx, cy, r, 12, 0.72), fill=secondary, color=stroke, w=lw * 0.7))
        parts.append(poly(_star(cx, cy, r * 0.5, 12, 0.5, math.pi / 12), fill=accent, color=stroke, w=lw * 0.6))
        for i in range(12):
            a = TAU * i / 12
            x1, y1 = cx + r * 0.5 * math.cos(a), cy + r * 0.5 * math.sin(a)
            x2, y2 = cx + r * math.cos(a), cy + r * math.sin(a)
            parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{lw * 0.5}"/>')
    elif p.style == "squares":
        steps = 4
        for i in range(steps, 0, -1):
            rr = r * i / steps
            rot = math.pi / 4 * ((steps - i) % 2)
            parts.append(poly(_polygon(cx, cy, rr, 4, rot),
                              fill="none",
                              color=accent if i % 2 == 0 else stroke,
                              w=lw * (1.2 if i == steps else 0.8)))
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.1:.2f}" fill="{secondary}"/>')
    elif p.style == "braid":
        # Interlaced band: S-curves across the tile.
        parts.append(f'<path d="M0,{cy} C{t * 0.25:.1f},{cy - t * 0.3:.1f} {t * 0.75:.1f},{cy + t * 0.3:.1f} {t},{cy}" '
                     f'stroke="{stroke}" stroke-width="{lw * 1.6}" fill="none"/>')
        parts.append(f'<path d="M0,{cy} C{t * 0.25:.1f},{cy + t * 0.3:.1f} {t * 0.75:.1f},{cy - t * 0.3:.1f} {t},{cy}" '
                     f'stroke="{accent}" stroke-width="{lw * 1.6}" fill="none"/>')
        k = rng.choice([0.28, 0.36, 0.44])
        parts.append(poly(_star(cx, cy, t * k, 8, 0.5, rng.random() * TAU), fill="none", color=secondary))
    else:
        raise ValueError(f"unknown pattern style: {p.style}")
    return "".join(parts)


def render_pattern_svg(p: PatternParams) -> str:
    """Render a full tiled SVG pattern."""
    rng = random.Random(p.seed)
    c = p.resolve_colors()
    bg = p.background if p.background is not None else c[3]
    t = max(40, int(p.tile))
    W = t * p.cols
    H = t * p.rows

    # Seed-driven global rotation adds variety across variants.
    rot = rng.uniform(-0.06, 0.06) if p.style in ("khatam8", "star12") else 0.0
    tile = _tile_svg(p, rng)

    transform = f' transform="rotate({math.degrees(rot):.3f} {W / 2} {H / 2})"' if rot else ""
    defs = f'<defs><pattern id="mishkat-tile" width="{t}" height="{t}" patternUnits="userSpaceOnUse">{tile}</pattern></defs>'
    bgrect = f'<rect width="{W}" height="{H}" fill="{bg}"/>' if bg else ""
    border = (f'<rect x="6" y="6" width="{W - 12}" height="{H - 12}" fill="none" '
              f'stroke="{c[0]}" stroke-width="3"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">{defs}{bgrect}'
            f'<rect width="{W}" height="{H}" fill="url(#mishkat-tile)"{transform}/>{border}</svg>')


def variants(p: PatternParams, count: int = 6) -> list[dict]:
    """Generate `count` variant descriptors (different seeds / rotations)."""
    rng = random.Random(p.seed)
    out = []
    for _ in range(max(1, min(count, 24))):
        s = rng.randrange(1, 10_000)
        q = PatternParams(**{**p.__dict__, "seed": s})
        out.append({
            "seed": s,
            "style": q.style,
            "svg": render_pattern_svg(q),
        })
    return out
