# fontmetrics_extract_tags.py

from typing import Dict, Tuple


def _compute_basic_metrics(
    bbox: Tuple[int, int, int, int],
    width: int,
    lsb: int,
    rsb: int,
) -> Dict[str, float]:
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


def _classify_horizontal_weight(metrics: Dict[str, float]):
    lsb = metrics["lsb"]
    rsb = metrics["rsb"]
    width = metrics["width"]

    if width <= 0:
        return False, False, True

    diff = lsb - rsb
    threshold = 0.08 * width

    if abs(diff) <= threshold:
        return False, False, True

    if diff > 0:
        return True, False, False
    else:
        return False, True, False


def _detect_overhang_right(metrics: Dict[str, float]) -> bool:
    return metrics["rsb"] < 0.0


def compute_semantic_tags(
    glyph,
    glyph_set,
    bbox: Tuple[int, int, int, int],
    width: int,
    lsb: int,
    rsb: int,
) -> Dict[str, bool]:
    metrics = _compute_basic_metrics(bbox, width, lsb, rsb)

    has_left_weight, has_right_weight, is_symmetric = _classify_horizontal_weight(metrics)
    has_overhang_right = _detect_overhang_right(metrics)

    return {
        "has_left_weight": has_left_weight,
        "has_right_weight": has_right_weight,
        "is_symmetric": is_symmetric,
        "has_overhang_right": has_overhang_right,
    }
    