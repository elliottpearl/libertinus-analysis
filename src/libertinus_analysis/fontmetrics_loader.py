# fontmetrics_loader.py
#
# Lightweight loader/writer for the JSON fontmetrics data.
# This module does NOT extract metrics from font files — it only
# reads and writes the JSON files in data/fontmetrics/.
#
# It is designed to sit beside font_context.py and follow the
# package's config conventions.

from __future__ import annotations
from pathlib import Path
import json

from .config import FONTMETRICS_DIR


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# Saving (explicit only)
# ----------------------------------------------------------------------

def save_fontmetrics(style: str, data: dict) -> None:
    """
    Overwrite the JSON file for a given style.
    This function is NEVER called implicitly — only when explicitly requested.
    """
    path = FONTMETRICS_DIR / f"{style}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


# ----------------------------------------------------------------------
# Helper accessors
# ----------------------------------------------------------------------

def get_glyph(metrics: dict, cp: str) -> dict | None:
    """
    Return glyph metrics for a given codepoint ("0x0041"), or None.
    """
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

    # bbox = [xmin, ymin, xmax, ymax]
    xmin, ymin, xmax, ymax = bbox
    return (xmin + xmax) // 2
    