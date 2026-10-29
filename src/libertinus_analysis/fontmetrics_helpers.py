# fontmetrics_helpers.py
from __future__ import annotations

from .fontmetrics_loader import (
    get_bbox,
    get_anchor,
)

import math
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
# Anchor candidates: aya, bya, and X by the anchor model
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

# Italic angle per style (tan theta); roman styles have no slant.
SLOPE = {
    "regular": 0.0,
    "italic": math.tan(math.radians(12)),
    "semibold": 0.0,
    "semibold_italic": math.tan(math.radians(11.5)),
}

# Semibold italic anchor model: anchors are left of the lane midline by K,
# per anchor class ("0" above, "2" below). Other styles have K = 0.
SHIFT_K = {"semibold_italic": {"0": 150, "2": -12}}

def get_anchor_candidate(style_key: str, style_metrics: dict, cp: int, anchor_id: str):
    """
    Candidate (x, y) for the above ("0") or below ("2") anchor, per the
    anchor model in ANCHOR-HEURISTICS.md.

    y: edge of the ideal bounding box plus/minus the clearance (get_aya/get_bya).
    x: roman → bbox midpoint; italic → W/2 + y tan(theta) - K, at the
    candidate's own height.

    Returns (x, y, ideal) with ideal the aspect string, or None if the glyph
    has no bbox.
    """
    entry = style_metrics["codepoint"].get(cp)
    if not entry or not entry.get("bbox"):
        return None

    xmin, ymin, xmax, ymax = entry["bbox"]
    if anchor_id == "0":
        ideal = get_ideal_above_aspect(style_key, ymax, cp)
        y = get_aya(style_key, ideal)
    else:
        ideal = get_ideal_below_aspect(style_key, ymin)
        y = get_bya(style_key, ideal)
    if y is None:
        return None

    slope = SLOPE[style_key]
    if slope == 0.0:
        x = (xmin + xmax) / 2.0
    else:
        k = SHIFT_K.get(style_key, {}).get(anchor_id, 0)
        x = entry["width"] / 2.0 + y * slope - k
    return x, y, ideal

# Mark anchor height relative to the mark's own outline, per anchor class:
# above ("0", semibold also "1") is this far above the outline's bottom, below
# ("2") this far below its top. Medians of each style's MARK_ABOVE / MARK_BELOW.
# Semibold's class 1 (dot, diaeresis, ring, hook, comma above) pairs with lower
# base anchors (n: 550 vs 646), so its marks sit equally far above the base.
MARK_ANCHOR_OFFSET_OPT = {
    "regular":        {"0": 143, "2": 46},
    "italic":         {"0": 142, "2": 48},
    "semibold":       {"0": 157, "1": 60, "2": 54},
    "semibold_italic":{"0": 147, "2": 54},
}

def get_mark_anchor_candidate(style_key: str, style_metrics: dict, cp: int, anchor_id: str):
    """
    Candidate (x, y) for a mark's anchor in class anchor_id.

    y: above-marks → bbox ymin + offset; below-marks → bbox ymax - offset
    (MARK_ANCHOR_OFFSET_OPT), so every mark keeps the same gap to the base.
    x: on the mark's own axis at that height, axis_x + y tan(theta) - K.

    Returns None if the glyph is missing or the class has no offset.
    """
    entry = style_metrics["codepoint"].get(cp)
    offset = MARK_ANCHOR_OFFSET_OPT[style_key].get(anchor_id)
    if not entry or not entry.get("bbox") or offset is None:
        return None

    xmin, ymin, xmax, ymax = entry["bbox"]
    y = ymax - offset if anchor_id == "2" else ymin + offset
    k = SHIFT_K.get(style_key, {}).get(anchor_id, 0)
    x = entry["axis_x"] + y * SLOPE[style_key] - k
    return x, y
