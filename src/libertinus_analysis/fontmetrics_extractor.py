# fontmetrics_extractor.py
#
# Extract bbox, anchors, and horizontal metrics (width, lsb, rsb)
# for all glyphs in a font, and write them to data/fontmetrics/<font_key>.json.

import json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

from .font_context import extract_mark_attachment_data
from .font_context import FONTS


# ------------------------------------------------------------
# JSON helpers
# ------------------------------------------------------------

def load_fontmetrics_json(font_key):
    """
    Load data/fontmetrics/<font_key>.json.
    Returns {"glyphs": {}, "_orphans": {}} if missing.
    """
    path = Path("data/fontmetrics") / f"{font_key}.json"
    if not path.exists():
        return {"glyphs": {}, "_orphans": {}}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_fontmetrics_json(font_key, data):
    """
    Write JSON to data/fontmetrics/<font_key>.json.
    """
    path = Path("data/fontmetrics") / f"{font_key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ------------------------------------------------------------
# Bounding box extraction
# ------------------------------------------------------------

def get_glyph_bbox(glyph_set, glyph_name):
    """
    Return (xMin, yMin, xMax, yMax) for a glyph.
    """
    g = glyph_set[glyph_name]
    pen = BoundsPen(glyph_set)
    g.draw(pen)
    if pen.bounds is None:
        return (0, 0, 0, 0)
    xMin, yMin, xMax, yMax = pen.bounds
    return (round(xMin), round(yMin), round(xMax), round(yMax))


# ------------------------------------------------------------
# Main extractor
# ------------------------------------------------------------

def extract_fontmetrics(font_key, lookup_index):
    """
    Extract bbox + anchors + horizontal metrics for all glyphs.

    Returns a dict suitable for JSON serialization:

    {
        "glyphs": { "0x0041": {...}, ... },
        "_orphans": { "glyphName": {...}, ... }
    }
    """
    font_path = FONTS[font_key]["path"]

    ttfont = TTFont(font_path)
    glyph_set = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()

    # Extract anchors from GPOS
    markClassByGlyph, anchorsByBaseGlyph, _ = extract_mark_attachment_data(
        ttfont, lookup_index
    )

    out = {"glyphs": {}, "_orphans": {}}

    # Reverse cmap: glyph → [codepoints]
    rev_cmap = {}
    for cp, gname in cmap.items():
        rev_cmap.setdefault(gname, []).append(cp)

    # Iterate through all glyphs
    for gname in ttfont.getGlyphOrder():
        # REMOVE: glyph = ttfont["glyf"][gname]

        bbox = get_glyph_bbox(glyph_set, gname)

        anchors = anchorsByBaseGlyph.get(gname, {})
        anchors_json = {
            str(classIndex): [anchor.XCoordinate, anchor.YCoordinate]
            for classIndex, anchor in anchors.items()
        }

        width, lsb = ttfont["hmtx"].metrics[gname]
        rsb = width - lsb - (bbox[2] - bbox[0])

        entry = {
            "glyph": gname,
            "bbox": list(bbox),
            "anchors": anchors_json,
            "width": width,
            "lsb": lsb,
            "rsb": rsb,
            "tags": {}
        }

        if gname in rev_cmap:
            # Encoded glyph(s)
            for cp in rev_cmap[gname]:
                key = f"0x{cp:04X}"
                out["glyphs"][key] = entry
        else:
            # Unencoded glyph
            out["_orphans"][gname] = entry

    return out
    