"""SVG text renderer for shaped Arabic strings.

Uses arabic-reshaper + python-bidi to produce presentation forms in visual
order, then emits a standalone SVG document. Fonts are embedded as data URIs
so exports are portable and the browser preview matches exactly.
"""
from __future__ import annotations

import base64
import math
from pathlib import Path

from ..config import FONT_DIR
from ..arabic import shape

STYLES: dict[str, dict] = {
    # key: (file, label, fallback_size, line_height, letter_spacing, weight)
    "naskh": ("Amiri-Regular.ttf", "Naskh", 120, 1.75, 0, 400),
    "naskh_bold": ("Amiri-Bold.ttf", "Naskh Bold", 120, 1.75, 0, 700),
    "thuluth_like": ("ScheherazadeNew-Regular.ttf", "Thuluth-like", 130, 1.6, -2, 400),
    "ruqaa": ("ArefRuqaa-Regular.ttf", "Ruq'ah", 115, 1.55, 0, 400),
    "kufi": ("ReemKufi.ttf", "Kufi", 110, 1.5, 2, 500),
    "diwani_like": ("Katibeh-Regular.ttf", "Diwani-like", 140, 1.35, 0, 400),
    "decorative": ("Rakkas-Regular.ttf", "Decorative", 125, 1.5, 0, 400),
}
DEFAULT_STYLE = "naskh"


def _font_path(style_key: str) -> Path:
    fname = STYLES.get(style_key, STYLES[DEFAULT_STYLE])[0]
    p = FONT_DIR / fname
    if not p.exists():
        fallback = FONT_DIR / STYLES[DEFAULT_STYLE][0]
        if fallback.exists():
            return fallback
    return p


def _font_data_uri(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:font/ttf;base64,{b64}"


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def measure(text: str, style_key: str, font_size: float) -> float:
    """Approximate advance width for layout math (character-average heuristic)."""
    fname = STYLES.get(style_key, STYLES[DEFAULT_STYLE])[0]
    p = FONT_DIR / fname
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(str(p), fontNumber=0, lazy=True)
        cmap = font.getBestCmap()
        hmtx = font["hmtx"]
        units_per_em = font["head"].unitsPerEm
        shaped = shape(text)
        total = 0
        for ch in shaped:
            gid = cmap.get(ord(ch))
            if gid is None:
                continue
            total += hmtx[gid][0]
        # Arabic glyphs typically sit slightly above the raw advance sum.
        return (total / units_per_em) * font_size * 0.95
    except Exception:
        # Rough fallback: 0.55em average per code point.
        return max(1, len(text)) * font_size * 0.55


def render_text_svg(
    text: str,
    style_key: str = DEFAULT_STYLE,
    font_size: float = 120,
    fill: str = "#1c1c1c",
    background: str | None = "#f7f3e8",
    padding: float = 64,
    max_width: float = 1600,
    multiline: bool = True,
) -> str:
    """Render shaped Arabic text to a standalone SVG string."""
    lines = [text] if not multiline or "\n" not in text else text.split("\n")
    shaped_lines = [shape(ln) for ln in lines]
    fs = float(font_size)
    meta = STYLES.get(style_key, STYLES[DEFAULT_STYLE])
    line_h = fs * meta[3]

    # Wrap lines that exceed max_width using approximate measurement.
    if multiline and max_width:
        wrapped: list[str] = []
        for ln in lines:
            if measure(ln, style_key, fs) <= max_width:
                wrapped.append(ln)
                continue
            words = ln.split(" ")
            cur = ""
            for w in words:
                trial = (cur + " " + w).strip()
                if measure(trial, style_key, fs) > max_width and cur:
                    wrapped.append(cur)
                    cur = w
                else:
                    cur = trial
            if cur:
                wrapped.append(cur)
        shaped_lines = [shape(ln) for ln in wrapped]

    lh = fs * meta[3]
    block_h = lh * len(shaped_lines)
    W = int(max_width + 2 * padding)
    H = int(block_h + 2 * padding + fs * 0.35)

    tspans = []
    for i, sl in enumerate(shaped_lines):
        y = padding + fs + i * lh
        tspans.append(
            f'<tspan x="{W / 2}" y="{y:.1f}" text-anchor="middle">{_esc(sl)}</tspan>'
        )

    bg = f'<rect width="{W}" height="{H}" fill="{_esc(background)}"/>' if background else ""
    font_uri = ""
    fp = _font_path(style_key)
    if fp.exists():
        font_uri = f"@font-face {{ font-family:'MishkatFont'; src:url('{_font_data_uri(fp)}') format('truetype'); }}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs><style>{font_uri}
    text {{ font-family:'MishkatFont'; font-size:{fs}px; font-weight:{meta[5]}; letter-spacing:{meta[4]}px; fill:{_esc(fill)}; direction:ltr; unicode-bidi:bidi-override; }}</style></defs>
  {bg}
  <text x="{W / 2}" y="{padding + fs}">
    {''.join(tspans)}
  </text>
</svg>"""
