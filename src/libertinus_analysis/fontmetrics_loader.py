# fontmetrics_loader.py

from __future__ import annotations
from pathlib import Path
import json

from .config import FONTMETRICS_DIR


def load_fontmetrics(style: str) -> dict:
    """
    Load metrics JSON for a single font style.
    Returns a dict keyed by codepoint strings ("0x0041").
    """
    path = FONTMETRICS_DIR / f"{style}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fontmetrics file not found: {path}")

    return json.loads(path.read_text())


def load_all_fontmetrics() -> dict[str, dict]:
    """
    Load metrics for all known styles.
    Returns a dict: {style: metrics_dict}.
    """
    styles = ["regular", "italic", "semibold", "semibold_italic"]
    return {style: load_fontmetrics(style) for style in styles}


def get_glyph(metrics: dict, cp: str) -> dict | None:
    return metrics.get(cp)


def get_anchor(style_metrics, cp, anchor_name):
    glyphs = style_metrics.get("glyphs", {})
    entry = glyphs.get(cp)
    if not entry:
        return None
    anchors = entry.get("anchors", {})
    return anchors.get(anchor_name)


def get_bbox_x_mid(style_metrics, cp):
    glyphs = style_metrics.get("glyphs", {})
    entry = glyphs.get(cp)
    if not entry:
        return None
    bbox = entry.get("bbox")
    if not bbox:
        return None
    xmin, ymin, xmax, ymax = bbox
    return (xmin + xmax) // 2
    