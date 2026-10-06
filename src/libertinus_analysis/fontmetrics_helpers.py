# fontmetrics_helpers.py
from __future__ import annotations

from .fontmetrics_loader import (
    get_bbox,
    get_anchor,
)

import unicodedata

# ----------------------------------------------------------------------
# Style-specific vertical thresholds (from BlueValues + tolerances)
# ----------------------------------------------------------------------

VERTICAL_THRESHOLDS = {
    "regular": {
        "ascender_min": 688 - 6,   # 682
        "capital_min": 645 - 5,    # 640
        "xheight_min": 429 - 3,    # 426
        "baseline_max": 0 + 2,     # 2
        "descender_max": -238 + 3, # -235
    },
    "italic": {
        "ascender_min": 688 - 6,   # 682
        "capital_min": 645 - 5,    # 640
        "xheight_min": 429 - 3,    # 426
        "baseline_max": 0 + 2,     # 2
        "descender_max": -238 + 3, # -235
    },
    "semibold": {
        "ascender_min": 690 - 6,   # 684
        "capital_min": 645 - 5,    # 640
        "xheight_min": 433 - 3,    # 430
        "baseline_max": 0 + 2,     # 2
        "descender_max": -238 + 3, # -235
    },
    "semibold_italic": {
        "ascender_min": 696 - 6,   # 690
        "capital_min": 645 - 5,    # 640
        "xheight_min": 434 - 3,    # 431
        "baseline_max": 0 + 2,     # 2
        "descender_max": -239 + 3, # -236
    },
}

# ----------------------------------------------------------------------
# Anchor Y references (Table 9)
# ----------------------------------------------------------------------

ANCHOR_Y_REF = {
    "regular": {
        "ascender": 885,
        "capital": 850,
        "xheight": 645,
        "baseline": -110,
        "descender": -319,
    },
    "italic": {
        "ascender": 890,
        "capital": 850,
        "xheight": 645,
        "baseline": -110,
        "descender": -319,
    },
    "semibold": {
        "ascender": 885,
        "capital": 805,
        "xheight": 645,
        "baseline": -110,
        "descender": -319,
    },
    "semibold_italic": {
        "ascender": 890,
        "capital": 850,
        "xheight": 645,
        "baseline": -110,
        "descender": -319,
    },
}

# --- New optical thresholds per style (do NOT replace legacy dicts) ---

VERTICAL_THRESHOLDS_OPT = {
    "reg": {
        "asc": {"val": 698, "lo": 688, "hi": 698},
        "cap": {"val": 645, "lo": 645, "hi": 658},
        "xh":  {"val": 429, "lo": 429, "hi": 442},
        "base":{"val":   0, "lo": -12, "hi":   0},
        "desc":{"val": -232, "lo": -238, "hi": -227},
    },
    "it": {
        "asc": {"val": 698, "lo": 688, "hi": 698},
        "cap": {"val": 645, "lo": 645, "hi": 658},
        "xh":  {"val": 429, "lo": 429, "hi": 442},
        "base":{"val":   0, "lo": -12, "hi":   1},
        "desc":{"val": -232, "lo": -238, "hi": -227},
    },
    "sb": {
        "asc": {"val": 698, "lo": 690, "hi": 698},
        "cap": {"val": 645, "lo": 645, "hi": 662},
        "xh":  {"val": 434, "lo": 433, "hi": 447},
        "base":{"val":   0, "lo": -12, "hi":   1},
        "desc":{"val": -232, "lo": -238, "hi": -212},
    },
    "si": {
        "asc": {"val": 698, "lo": 696, "hi": 705},
        "cap": {"val": 645, "lo": 645, "hi": 662},
        "xh":  {"val": 434, "lo": 434, "hi": 447},
        "base":{"val":   0, "lo": -20, "hi":   0},
        "desc":{"val": -232, "lo": -239, "hi": -219},
    },
}

ANCHOR_Y_REF_OPT = {
    "reg": {"asc": 885, "cap": 850, "xh": 645, "base": -110, "desc": -319},
    "it":  {"asc": 890, "cap": 850, "xh": 645, "base": -110, "desc": -319},
    "sb":  {"asc": 885, "cap": 805, "xh": 645, "base": -110, "desc": -319},
    "si":  {"asc": 890, "cap": 850, "xh": 645, "base": -110, "desc": -319},
}

CLEARANCES_OPT = {
    "reg": {"asc": 187, "cap": 205, "xh": 216, "base": 110, "desc": 87},
    "it":  {"asc": 192, "cap": 205, "xh": 216, "base": 110, "desc": 87},
    "sb":  {"asc": 187, "cap": 205, "xh": 211, "base": 110, "desc": 87},
    "si":  {"asc": 192, "cap": 205, "xh": 211, "base": 110, "desc": 87},
}

def get_unicode_category(cp: int) -> str:
    if cp in (0x0294, 0x0295, 0x0296):
        return "Lu"
    return unicodedata.category(chr(cp))

def _within_range(val: int, lo: int, hi: int) -> bool:
    return lo <= val <= hi

def get_ideal_above_aspect(style_key: str, ymax: int, cp: int) -> str:
    cat = get_unicode_category(cp)
    thresholds = VERTICAL_THRESHOLDS_OPT[style_key]

    if cat == "Lu":
        candidates = ["c", "a"]
    else:
        candidates = ["x", "a"]

    aspect_map = {
        "a": thresholds["asc"],
        "c": thresholds["cap"],
        "x": thresholds["xh"],
    }

    best_aspect = None
    best_delta = None
    for code in candidates:
        t = aspect_map[code]
        delta = ymax - t["val"]
        if best_delta is None or abs(delta) < abs(best_delta):
            best_aspect = code
            best_delta = delta

    t = aspect_map[best_aspect]
    if _within_range(ymax, t["lo"], t["hi"]):
        return best_aspect

    if best_delta == 0:
        return best_aspect
    sign = "+" if best_delta > 0 else "-"
    return f"{best_aspect}{sign}{abs(best_delta)}"

def get_ideal_below_aspect(style_key: str, ymin: int) -> str:
    thresholds = VERTICAL_THRESHOLDS_OPT[style_key]

    base = thresholds["base"]
    desc = thresholds["desc"]

    delta_b = ymin - base["val"]
    delta_d = ymin - desc["val"]

    if abs(delta_b) <= abs(delta_d):
        code = "b"
        t = base
        delta = delta_b
    else:
        code = "d"
        t = desc
        delta = delta_d

    if _within_range(ymin, t["lo"], t["hi"]):
        return code

    if delta == 0:
        return code
    sign = "+" if delta > 0 else "-"
    return f"{code}{sign}{abs(delta)}"


# ----------------------------------------------------------------------
# BBox-derived metrics
# ----------------------------------------------------------------------

def get_outline_center_and_width(style_metrics: dict, cp: int):
    """
    Return (center_x, width) of the glyph outline from its bbox.
    center_x = (xmin + xmax) / 2
    width    = xmax - xmin
    """
    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None, None

    xmin, ymin, xmax, ymax = bbox
    center = (xmin + xmax) / 2
    width = xmax - xmin
    return center, width


def get_bbox_mid_x(style_metrics: dict, cp: int):
    """
    Legacy helper: midpoint of the bbox in x-direction (upright only).
    """
    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None

    xmin, ymin, xmax, ymax = bbox
    return (xmin + xmax) // 2

# ----------------------------------------------------------------------
# Vertical classification (Table 9 ranges)
# ----------------------------------------------------------------------

def classify_vertical(style_key: str, bbox):
    """
    Classify glyph into one of:
        ascender, capital, xheight, descender, baseline
    using BlueValues-derived thresholds.
    """
    xmin, ymin, xmax, ymax = bbox
    T = VERTICAL_THRESHOLDS.get(style_key, VERTICAL_THRESHOLDS["regular"])

    if ymax >= T["ascender_min"]:
        return "ascender"
    if ymax >= T["capital_min"]:
        return "capital"
    if ymax >= T["xheight_min"]:
        return "xheight"
    if ymin <= T["descender_max"]:
        return "descender"
    return "baseline"


def get_anchor_y_ref(style_key: str, category: str, above: bool) -> int:
    """
    Look up the anchor Y reference for the given style and vertical category.
    above=True  → use ascender/capital/xheight
    above=False → use baseline/descender
    """
    refs = ANCHOR_Y_REF.get(style_key, ANCHOR_Y_REF["regular"])

    if above:
        if category == "ascender":
            return refs["ascender"]
        if category == "capital":
            return refs["capital"]
        if category == "xheight":
            return refs["xheight"]
        return refs["capital"]
    else:
        if category == "descender":
            return refs["descender"]
        return refs["baseline"]

# ----------------------------------------------------------------------
# Style-aware midpoints
# ----------------------------------------------------------------------

def get_upright_mid_x(style_metrics: dict, cp: int):
    """
    Upright geometric midpoint of bbox in x-direction.
    """
    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None

    xmin, ymin, xmax, ymax = bbox
    return (xmin + xmax) / 2.0


def get_slanted_mid_x(style_key: str, style_metrics: dict, cp: int, above: bool):
    """
    Slant-corrected geometric midpoint for italic/semibold_italic,
    at the appropriate anchor Y reference (above or below).
    """
    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None

    xmin, ymin, xmax, ymax = bbox
    xm_upright = (xmin + xmax) / 2.0
    ym_mid = (ymin + ymax) / 2.0

    category = classify_vertical(style_key, bbox)
    y_ref = get_anchor_y_ref(style_key, category, above=above)

    if style_key == "italic":
        slant = 0.2126  # tan(12°)
    elif style_key == "semibold_italic":
        slant = 0.2037  # tan(11.5°)
    else:
        slant = 0.0

    return xm_upright + slant * (y_ref - ym_mid)


def get_mid_x_for_style(style_key: str, style_metrics: dict, cp: int, anchor_id: str):
    """
    Unified midpoint helper:
        regular/semibold → upright midpoint (xm)
        italic/semibold_italic → slanted midpoint (axm/bxm)
    anchor_id "0" → above; "2" → below.
    """
    if style_key in ("italic", "semibold_italic"):
        above = (anchor_id == "0")
        return get_slanted_mid_x(style_key, style_metrics, cp, above=above)
    else:
        return get_upright_mid_x(style_metrics, cp)

# ----------------------------------------------------------------------
# Anchor-derived metrics
# ----------------------------------------------------------------------

def compute_dx(style_metrics: dict, cp: int, anchor_id: str, style_key: str):
    """
    Compute:
        dx = anchor_x - geometric_mid_x(style, anchor_id)

    Returns dx, or None if missing data.
    """
    anchor = get_anchor(style_metrics, cp, anchor_id)
    if not anchor:
        return None

    mid_x = get_mid_x_for_style(style_key, style_metrics, cp, anchor_id)
    if mid_x is None:
        return None

    anchor_x = anchor[0]
    dx = anchor_x - mid_x
    return dx

