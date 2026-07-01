# fontmetrics_helpers.py
from __future__ import annotations

from .fontmetrics_loader import (
    get_bbox,
    get_anchor,
)

# ----------------------------------------------------------------------
# Style-specific vertical thresholds (derived from Table 9)
# ----------------------------------------------------------------------

VERTICAL_THRESHOLDS = {
    "regular": {
        "ascender_min": 680,
        "capital_min": 640,
        "xheight_min": 420,
        "baseline_max": 10,
        "descender_max": -220,
    },
    "italic": {
        "ascender_min": 680,
        "capital_min": 640,
        "xheight_min": 420,
        "baseline_max": 10,
        "descender_max": -220,
    },
    "semibold": {
        "ascender_min": 685,
        "capital_min": 635,
        "xheight_min": 425,
        "baseline_max": 10,
        "descender_max": -225,
    },
    "semibold_italic": {
        "ascender_min": 690,
        "capital_min": 635,
        "xheight_min": 425,
        "baseline_max": 10,
        "descender_max": -225,
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
    using style-specific thresholds derived from Table 9.
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
        # fallback
        return refs["capital"]
    else:
        if category == "descender":
            return refs["descender"]
        # baseline or fallback
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
