# fontmetrics_helpers.py
from __future__ import annotations

from .fontmetrics_loader import (
    get_bbox,
    get_anchor,
)

import unicodedata

# ----------------------------------------------------------------------
# Optical thresholds per style (BlueValues + tolerances, legacy style keys)
# ----------------------------------------------------------------------

VERTICAL_THRESHOLDS_OPT = {
    "regular": {
        "asc": {"val": 698, "lo": 688, "hi": 698},
        "cap": {"val": 645, "lo": 645, "hi": 658},
        "xh":  {"val": 429, "lo": 429, "hi": 442},
        "base":{"val":   0, "lo": -12, "hi":   0},
        "desc":{"val": -232, "lo": -238, "hi": -227},
    },
    "italic": {
        "asc": {"val": 698, "lo": 688, "hi": 698},
        "cap": {"val": 645, "lo": 645, "hi": 658},
        "xh":  {"val": 429, "lo": 429, "hi": 442},
        "base":{"val":   0, "lo": -12, "hi":   1},
        "desc":{"val": -232, "lo": -238, "hi": -227},
    },
    "semibold": {
        "asc": {"val": 698, "lo": 690, "hi": 698},
        "cap": {"val": 645, "lo": 645, "hi": 662},
        "xh":  {"val": 434, "lo": 433, "hi": 447},
        "base":{"val":   0, "lo": -12, "hi":   1},
        "desc":{"val": -232, "lo": -238, "hi": -212},
    },
    "semibold_italic": {
        "asc": {"val": 698, "lo": 696, "hi": 705},
        "cap": {"val": 645, "lo": 645, "hi": 662},
        "xh":  {"val": 434, "lo": 434, "hi": 447},
        "base":{"val":   0, "lo": -20, "hi":   0},
        "desc":{"val": -232, "lo": -239, "hi": -219},
    },
}

ANCHOR_Y_REF_OPT = {
    "regular":        {"asc": 885, "cap": 850, "xh": 645, "base": -110, "desc": -319},
    "italic":         {"asc": 890, "cap": 850, "xh": 645, "base": -110, "desc": -319},
    "semibold":       {"asc": 885, "cap": 805, "xh": 645, "base": -110, "desc": -319},
    "semibold_italic":{"asc": 890, "cap": 850, "xh": 645, "base": -110, "desc": -319},
}

CLEARANCES_OPT = {
    "regular":        {"asc": 187, "cap": 205, "xh": 216, "base": 110, "desc": 87},
    "italic":         {"asc": 192, "cap": 205, "xh": 216, "base": 110, "desc": 87},
    "semibold":       {"asc": 187, "cap": 160, "xh": 211, "base": 110, "desc": 87},
    "semibold_italic":{"asc": 192, "cap": 205, "xh": 211, "base": 110, "desc": 87},
}

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def get_unicode_category(cp: int) -> str:
    if cp in (0x0294, 0x0295, 0x0296):
        return "Lu"
    return unicodedata.category(chr(cp))

def _within_range(val: int, lo: int, hi: int) -> bool:
    return lo <= val <= hi

# ----------------------------------------------------------------------
# Above/below aspect classification (aa / ba)
# ----------------------------------------------------------------------

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
# Vertical classification (OPT-only)
# ----------------------------------------------------------------------

def classify_vertical(style_key: str, bbox):
    """
    Classify glyph into one of:
        ascender, capital, xheight, descender, baseline
    using OPT BlueValues thresholds.
    """
    xmin, ymin, xmax, ymax = bbox
    T = VERTICAL_THRESHOLDS_OPT[style_key]

    if ymax >= T["asc"]["lo"]:
        return "ascender"
    if ymax >= T["cap"]["lo"]:
        return "capital"
    if ymax >= T["xh"]["lo"]:
        return "xheight"
    if ymin <= T["desc"]["hi"]:
        return "descender"
    return "baseline"

def get_anchor_y_ref(style_key: str, category: str, above: bool) -> int:
    """
    Look up the anchor Y reference for the given style and vertical category,
    using OPT anchor references.
    above=True  → use ascender/capital/xheight
    above=False → use baseline/descender
    """
    refs = ANCHOR_Y_REF_OPT[style_key]

    if above:
        if category == "ascender":
            return refs["asc"]
        if category == "capital":
            return refs["cap"]
        if category == "xheight":
            return refs["xh"]
        return refs["cap"]
    else:
        if category == "descender":
            return refs["desc"]
        return refs["base"]

# ----------------------------------------------------------------------
# Style-aware midpoints (for dx)
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
    at the appropriate anchor Y reference (above or below), using OPT refs.
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
# Anchor-derived metrics (dx)
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

# ----------------------------------------------------------------------
# New helpers: aya, bya, axm, bxm (Step 1, no padding)
# ----------------------------------------------------------------------

def _parse_aspect(aspect: str) -> tuple[str, int]:
    """
    Parse aspect strings like 'c', 'c+23', 'a-21', 'd+36' into (base, delta).
    """
    if "+" in aspect:
        base, delta_str = aspect.split("+", 1)
        delta = int(delta_str)
    elif "-" in aspect:
        base, delta_str = aspect.split("-", 1)
        delta = -int(delta_str)
    else:
        base = aspect
        delta = 0
    return base, delta

# Crude optical correction per aspect, applied only outside the threshold.
# The script does not know the glyph's shape at ymin/ymax, so a small
# overshoot is assumed. Ascenders are flat-topped: no correction.
OPTICAL_CORRECTION = {"asc": 0, "cap": 2, "xh": 2, "base": 2, "desc": 2}

def _candidate_anchor_y(style_key: str, aspect: str, aspect_map: dict, above: bool) -> int | None:
    """
    Shared logic for aya/bya.
    Within threshold (no delta in the aspect string) → snap to the reference.
    Otherwise → reference + delta, pulled toward the glyph by the optical
    correction (down for above anchors, up for below anchors).
    """
    if aspect is None:
        return None

    base, delta = _parse_aspect(aspect)
    if base not in aspect_map:
        return None

    ref_dict = ANCHOR_Y_REF_OPT.get(style_key)
    if ref_dict is None:
        return None

    key = aspect_map[base]
    y0 = ref_dict[key]
    if delta == 0:
        return y0

    corr = OPTICAL_CORRECTION[key]
    return y0 + delta - corr if above else y0 + delta + corr

def get_aya(style_key: str, aa: str) -> int | None:
    """
    Compute aya (above anchor Y) from aa string and optical anchor references.
    """
    return _candidate_anchor_y(style_key, aa, {"a": "asc", "c": "cap", "x": "xh"}, above=True)

def get_bya(style_key: str, ba: str) -> int | None:
    """
    Compute bya (below anchor Y) from ba string and optical anchor references.
    """
    return _candidate_anchor_y(style_key, ba, {"b": "base", "d": "desc"}, above=False)

def get_axm(style_key: str, style_metrics: dict, cp: int, aya: int | None) -> float | None:
    """
    Compute axm: slant-corrected midpoint X for the above anchor,
    relative to the optical aspect (aya).
    """
    if aya is None:
        return None

    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None

    xmin, ymin, xmax, ymax = bbox
    xm_upright = (xmin + xmax) / 2.0
    ym_mid = (ymin + ymax) / 2.0

    if style_key == "italic":
        slant = 0.2126  # tan(12°)
    elif style_key == "semibold_italic":
        slant = 0.2037  # tan(11.5°)
    else:
        slant = 0.0

    return xm_upright + slant * (aya - ym_mid)

def get_bxm(style_key: str, style_metrics: dict, cp: int, bya: int | None) -> float | None:
    """
    Compute bxm: slant-corrected midpoint X for the below anchor,
    relative to the optical aspect (bya).
    """
    if bya is None:
        return None

    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None

    xmin, ymin, xmax, ymax = bbox
    xm_upright = (xmin + xmax) / 2.0
    ym_mid = (ymin + ymax) / 2.0

    if style_key == "italic":
        slant = 0.2126  # tan(12°)
    elif style_key == "semibold_italic":
        slant = 0.2037  # tan(11.5°)
    else:
        slant = 0.0

    return xm_upright + slant * (bya - ym_mid)
