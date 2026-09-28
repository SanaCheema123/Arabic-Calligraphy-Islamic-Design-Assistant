"""Composition renderer: text + pattern combined into one SVG/PNG.

Builds the pattern layer directly (no string parsing) by asking the pattern
engine for its <defs> and tile markup separately.
"""
from __future__ import annotations

import math
import random

from ..arabic import shape
from ..patterns.generator import (
    PALETTES,
    PatternParams,
    _tile_svg,
)
from .svgtext import STYLES, DEFAULT_STYLE, _esc, _font_data_uri, _font_path


def _pattern_layer(pattern: PatternParams, W: int, H: int, opacity: float) -> tuple[str, str]:
    """Return (defs_fragment, rect_fragment) for the pattern layer."""
    rng = random.Random(pattern.seed)
    c = pattern.resolve_colors()
    t = max(40, int(pattern.tile))
    tile = _tile_svg(pattern, rng)
    defs = f'<defs><pattern id="mk-comp-tile" width="{t}" height="{t}" patternUnits="userSpaceOnUse">{tile}</pattern></defs>'
    rect = f'<rect width="{W}" height="{H}" fill="url(#mk-comp-tile)" opacity="{opacity}"/>'
    return defs, rect


def render_composition_svg(
    text: str = "",
    style_key: str = DEFAULT_STYLE,
    font_size: float = 120,
    text_fill: str = "#1c1c1c",
    background: str = "#f7f3e8",
    width: int = 1200,
    height: int = 1600,
    pattern: PatternParams | None = None,
    pattern_opacity: float = 0.12,
    text_position: str = "center",  # center | top | bottom
) -> str:
    """Full poster composition: optional pattern layer + centered Arabic text."""
    W, H = int(width), int(height)
    meta = STYLES.get(style_key, STYLES[DEFAULT_STYLE])
    fs = float(font_size)
    line_h = fs * meta[3]

    lines = (text or "").split("\n")
    shaped = [shape(ln) for ln in lines]
    block_h = line_h * len(shaped)

    if text_position == "top":
        base_y = fs + H * 0.08
    elif text_position == "bottom":
        base_y = H * 0.92 - block_h + fs
    else:
        base_y = (H - block_h) / 2 + fs * 0.85

    tspans = "".join(
        f'<tspan x="{W / 2}" y="{base_y + i * line_h:.1f}" '
        f'text-anchor="middle">{_esc(sl)}</tspan>'
        for i, sl in enumerate(shaped)
    )

    font_uri = ""
    fp = _font_path(style_key)
    if fp.exists():
        font_uri = (
            f"@font-face {{ font-family:'MishkatFont'; "
            f"src:url('{_font_data_uri(fp)}') format('truetype'); }}"
        )

    pattern_defs, pattern_rect = "", ""
    if pattern is not None:
        pattern_defs, pattern_rect = _pattern_layer(pattern, W, H, pattern_opacity)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs><style>{font_uri}
    text {{ font-family:'MishkatFont'; font-size:{fs}px; font-weight:{meta[5]}; letter-spacing:{meta[4]}px; fill:{_esc(text_fill)}; direction:ltr; unicode-bidi:bidi-override; }}</style>
  {pattern_defs}</defs>
  <rect width="{W}" height="{H}" fill="{_esc(background)}"/>
  {pattern_rect}
  <text x="{W / 2}" y="{base_y:.1f}">{tspans}</text>
</svg>"""
