# fontmetrics_extract_tags.py
#
# Compute anchor-useful semantic tags for a glyph.
#
# Public API (kept compatible with the existing extractor):
#
#     compute_semantic_tags(
#         glyph,
#         glyph_set,
#         bbox,
#         width,
#         lsb,
#         rsb,
#         style="roman",
#     ) -> dict
#
# The tags describe only horizontal visual weight and
# slant/overhang behavior:
#
#     has_left_weight
#     has_right_weight
#     is_symmetric
#     has_overhang_right
#     is_italic_slanted
#

from typing import Dict, Tuple


def _compute_basic_metrics(
    bbox: Tuple[int, int, int, int],
    width: int,
    lsb: int,
    rsb: int,
) -> Dict[str, float]:
    """
    Derive simple horizontal metrics from bbox and sidebearings.

    bbox: (xmin, ymin, xmax, ymax)
    width: advance width
    lsb, rsb: left/right sidebearings
    """
    xmin, _, xmax, _ = bbox
    outline_width = xmax - xmin
    bbox_center = (xmin + xmax) / 2.0

    return {
        "xmin": float(xmin),
        "xmax": float(xmax),
        "outline_width": float(outline_width),
        "bbox_center": float(bbox_center),
        "width": float(width),
        "lsb": float(lsb),
        "rsb": float(rsb),
    }


def _classify_horizontal_weight(metrics: Dict[str, float]) -> Tuple[bool, bool, bool]:
    """
    Decide has_left_weight, has_right_weight, is_symmetric based on
    simple horizontal metrics.

    We use sidebearings as a proxy for horizontal visual balance:

        - If lsb ≈ rsb → symmetric
        - If lsb > rsb → left-heavy
        - If rsb > lsb → right-heavy
    """
    lsb = metrics["lsb"]
    rsb = metrics["rsb"]
    width = metrics["width"]

    # If width is zero or tiny, treat as symmetric.
    if width <= 0:
        return False, False, True

    diff = lsb - rsb
    # Threshold as a fraction of width; tweakable if needed.
    threshold = 0.08 * width

    if abs(diff) <= threshold:
        # Balanced sidebearings → symmetric
        return False, False, True

    if diff > 0:
        # More space on the right → weight on the left
        return True, False, False
    else:
        # More space on the left → weight on the right
        return False, True, False


def _detect_overhang_right(metrics: Dict[str, float]) -> bool:
    """
    Detect right overhang: outline extends beyond advance width.

    In practice this is equivalent to rsb < 0.
    """
    return metrics["rsb"] < 0.0


def _detect_italic_slanted(style: str) -> bool:
    """
    Decide whether the glyph should be treated as italic-slanted.

    This is based on the font style label, not outline geometry.
    """
    style = (style or "").lower()
    return any(token in style for token in ("italic", "oblique"))


def compute_semantic_tags(
    glyph,
    glyph_set,
    bbox: Tuple[int, int, int, int],
    width: int,
    lsb: int,
    rsb: int,
    style: str = "roman",
) -> Dict[str, bool]:
    """
    Public entry point used by fontmetrics_extractor.build_glyph_entry.

    Parameters
    ----------
    glyph : Glyph
        The glyph object (currently unused, but kept for future refinements).
    glyph_set : Mapping[str, Glyph]
        The font's glyph set (currently unused here, but available if
        future tag logic needs outline access).
    bbox : (xmin, ymin, xmax, ymax)
        Glyph bounding box in font units.
    width : int
        Advance width.
    lsb, rsb : int
        Left and right sidebearings.
    style : str
        Style label, e.g. "regular", "italic", "semibold_italic".

    Returns
    -------
    Dict[str, bool]
        A dictionary with the five first-pass tags.
    """
    metrics = _compute_basic_metrics(bbox, width, lsb, rsb)

    has_left_weight, has_right_weight, is_symmetric = _classify_horizontal_weight(
        metrics
    )
    has_overhang_right = _detect_overhang_right(metrics)
    is_italic_slanted = _detect_italic_slanted(style)

    return {
        "has_left_weight": has_left_weight,
        "has_right_weight": has_right_weight,
        "is_symmetric": is_symmetric,
        "has_overhang_right": has_overhang_right,
        "is_italic_slanted": is_italic_slanted,
    }
