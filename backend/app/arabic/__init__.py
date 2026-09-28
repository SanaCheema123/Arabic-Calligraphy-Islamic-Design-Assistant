"""Arabic script utilities: validation, normalization and bidi shaping."""
from __future__ import annotations

import re
from dataclasses import dataclass

import arabic_reshaper
from bidi.algorithm import get_display

ARABIC_RANGE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
ARABIC_LETTER = re.compile(r"[\u0621-\u063A\u0641-\u064A\u0671-\u06D3]")
WHITESPACE = re.compile(r"\s+")

DIACRITICS = {
    "\u064B", "\u064C", "\u064D", "\u064E", "\u064F",
    "\u0650", "\u0651", "\u0652", "\u0670",
}

# Harakat that must sit *on top of* a base letter to be meaningful.
ORPHAN_MARKS = ("\u064B", "\u064C", "\u064D", "\u064E", "\u064F", "\u0650", "\u0652")


@dataclass
class TextIssue:
    code: str
    message: str
    severity: str = "warning"  # info | warning | error


def is_arabic(text: str) -> bool:
    return bool(ARABIC_RANGE.search(text or ""))


def arabic_letter_count(text: str) -> int:
    return len(ARABIC_LETTER.findall(text or ""))


def strip_diacritics(text: str) -> str:
    return "".join(ch for ch in (text or "") if ch not in DIACRITICS)


def normalize(text: str) -> str:
    """Light normalization for comparisons: strip diacritics/tatweel, unify forms."""
    t = strip_diacritics(text or "")
    t = t.replace("\u0640", "")  # tatweel
    t = (
        t.replace("\u0622", "\u0627")  # alef with madda -> alef
        .replace("\u0623", "\u0627")  # alef with hamza above -> alef
        .replace("\u0625", "\u0627")  # alef with hamza below -> alef
        .replace("\u0649", "\u064A")  # alef maqsura -> ya
        .replace("\u0629", "\u0647")  # ta marbuta -> ha
    )
    return WHITESPACE.sub(" ", t).strip()


def shape(text: str) -> str:
    """Convert logical-order Arabic into presentation forms for flat renderers."""
    reshaped = arabic_reshaper.reshape(text or "")
    return get_display(reshaped, base_dir="R")


def validate_text(text: str, max_chars: int = 120) -> list[TextIssue]:
    """Structural checks only. Semantic accuracy is the human reviewer's job."""
    issues: list[TextIssue] = []
    t = text or ""
    if not t.strip():
        issues.append(TextIssue("empty", "Text is empty.", "error"))
        return issues
    if len(t) > max_chars:
        issues.append(
            TextIssue("too_long", f"Text exceeds {max_chars} characters.", "error")
        )
    if not is_arabic(t):
        issues.append(
            TextIssue("no_arabic", "No Arabic characters detected.", "warning")
        )
    # Orphan diacritics: a harakat at the very start or doubled up.
    if t.startswith(ORPHAN_MARKS):
        issues.append(
            TextIssue("leading_harakat", "Text starts with an orphan diacritic.", "warning")
        )
    if re.search(r"[\u064B-\u0652]{2,}", t):
        issues.append(
            TextIssue("stacked_harakat", "Two or more consecutive diacritics.", "warning")
        )
    # Mixed-direction risk (e.g. Latin brand inside Arabic phrase).
    if re.search(r"[A-Za-z]", t) and is_arabic(t):
        issues.append(
            TextIssue("mixed_direction",
                      "Mixed Arabic/Latin text may reorder unexpectedly.",
                      "info")
        )
    return issues
