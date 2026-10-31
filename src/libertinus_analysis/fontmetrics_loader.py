# fontmetrics_loader.py

from __future__ import annotations
from functools import lru_cache

from .font_context import FONTS
from .fontmetrics_extractor import extract_fontmetrics

@lru_cache(maxsize=None)
def load_fontmetrics(font_key: str) -> dict:
    """
    Extract metrics for a single font_key from its font file, once per run,
    converting:
        "0x0250" → 0x0250 (int)
    The result is shared between callers; treat it as read-only.
    """
    raw = extract_fontmetrics(font_key, FONTS[font_key]["lookup_index"])

    # Convert codepoint keys "0xXXXX" → int
    cp_dict = {}
    for hex_key, rec in raw.get("codepoint", {}).items():
        cp_int = int(hex_key, 16)
        cp_dict[cp_int] = rec

    # glyph dictionary stays string‑keyed
    glyph_dict = raw.get("glyph", {})

    return {
        "codepoint": cp_dict,
        "glyph": glyph_dict,
    }

def load_all_fontmetrics() -> dict[str, dict]:
    font_keys = ["regular", "italic", "semibold", "semibold_italic"]
    return {fk: load_fontmetrics(fk) for fk in font_keys}

# ----------------------------------------------------------------------
# Accessors (raw only — no derived metrics here)
# ----------------------------------------------------------------------

def get_glyph(style_metrics: dict, cp: int) -> dict | None:
    return style_metrics["codepoint"].get(cp)


def get_anchor(style_metrics: dict, cp: int, anchor_name: str):
    entry = style_metrics["codepoint"].get(cp)
    if not entry:
        return None
    anchors = entry.get("anchors", {})
    return anchors.get(anchor_name)


def get_bbox(style_metrics: dict, cp: int):
    entry = style_metrics["codepoint"].get(cp)
    if not entry:
        return None
    return entry.get("bbox")
    