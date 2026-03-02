# fontmetrics_helpers.py

from __future__ import annotations

from .fontmetrics_loader import (
    get_bbox,
    get_anchor,
)


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
    Return the midpoint of the bbox in x-direction.
    """
    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None

    xmin, ymin, xmax, ymax = bbox
    return (xmin + xmax) // 2


# ----------------------------------------------------------------------
# Anchor-derived metrics
# ----------------------------------------------------------------------

def compute_dx(style_metrics: dict, cp: int, anchor_id: str):
    """
    Compute:
        dx      = anchor_x - outline_center_x
        dx_norm = dx / outline_width

    Returns (dx, dx_norm), or (None, None) if missing data.
    """
    anchor = get_anchor(style_metrics, cp, anchor_id)
    if not anchor:
        return None, None

    center, width = get_outline_center_and_width(style_metrics, cp)
    if center is None or width is None or width == 0:
        return None, None

    anchor_x = anchor[0]
    dx = anchor_x - center
    dx_norm = dx / width

    return dx, dx_norm