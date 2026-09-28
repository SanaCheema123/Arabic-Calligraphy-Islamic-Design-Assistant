"""Rasterize an SVG string to PNG bytes via cairosvg."""
from __future__ import annotations

import io

import cairosvg


def svg_to_png(svg: str, scale: float = 1.0, dpi: int = 300) -> bytes:
    """Render an SVG string to PNG bytes. `scale` multiplies the SVG size."""
    return cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        scale=scale,
        dpi=dpi,
    )


def svg_bytes_to_png(svg_bytes: bytes, scale: float = 1.0, dpi: int = 300) -> bytes:
    return cairosvg.svg2png(bytestring=svg_bytes, scale=scale, dpi=dpi)


def svg_to_png_safe(svg: str, scale: float = 1.0, dpi: int = 300) -> tuple[bytes, str | None]:
    """svg_to_png that never raises; returns (png_bytes, error_message)."""
    try:
        return svg_to_png(svg, scale, dpi), None
    except Exception as exc:  # pragma: no cover - depends on cairo presence
        return b"", f"PNG rasterization failed: {exc}"
