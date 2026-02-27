# fontmetrics_extractor.py
#
# Extract bbox, anchors, horizontal metrics (width, lsb, rsb),
# and semantic tags for:
#   - all BASE_COVERAGE codepoints (encoded glyphs)
#   - all base_small_capital_glyph names (unencoded small-cap bases)
#
# Writes JSON to data/fontmetrics/<font_key>.json.

import json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

from .font_context import extract_mark_attachment_data
from .font_context import FONTS

from data.ipa.ipa_unicode import BASE_COVERAGE, base_small_capital_glyph
from .fontmetrics_extract_tags import compute_semantic_tags


# ------------------------------------------------------------
# JSON helpers
# ------------------------------------------------------------

def load_fontmetrics_json(font_key):
    path = Path("data/fontmetrics") / f"{font_key}.json"
    if not path.exists():
        return {"codepoint": {}, "glyph": {}}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Upgrade old schema if needed
    if "codepoint" not in data and "glyphs" in data:
        data = {
            "codepoint": data.get("glyphs", {}),
            "glyph": data.get("_orphans", {}),
        }

    data.setdefault("codepoint", {})
    data.setdefault("glyph", {})

    return data


def write_fontmetrics_json(font_key, data):
    path = Path("data/fontmetrics") / f"{font_key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ------------------------------------------------------------
# Bounding box extraction
# ------------------------------------------------------------

def get_glyph_bbox(glyph_set, glyph_name):
    g = glyph_set[glyph_name]
    pen = BoundsPen(glyph_set)
    g.draw(pen)
    if pen.bounds is None:
        return (0, 0, 0, 0)
    xMin, yMin, xMax, yMax = pen.bounds
    return (round(xMin), round(yMin), round(xMax), round(yMax))


# ------------------------------------------------------------
# Per-glyph record builder
# ------------------------------------------------------------

def build_glyph_entry(ttfont, glyph_set, anchorsByBaseGlyph, gname, style="roman"):
    bbox = get_glyph_bbox(glyph_set, gname)

    anchors = anchorsByBaseGlyph.get(gname, {})
    anchors_json = {
        str(classIndex): [anchor.XCoordinate, anchor.YCoordinate]
        for classIndex, anchor in anchors.items()
    }

    width, lsb = ttfont["hmtx"].metrics[gname]
    rsb = width - lsb - (bbox[2] - bbox[0])

    tags = compute_semantic_tags(
        glyph_set[gname],
        glyph_set,
        bbox,
        width,
        lsb,
        rsb,
        style=style,
    )

    return {
        "glyph": gname,
        "bbox": list(bbox),
        "anchors": anchors_json,
        "width": width,
        "lsb": lsb,
        "rsb": rsb,
        "tags": tags,
    }


# ------------------------------------------------------------
# Main extractor
# ------------------------------------------------------------

def extract_fontmetrics(font_key, lookup_index, style="roman"):
    font_path = FONTS[font_key]["path"]

    ttfont = TTFont(font_path)
    glyph_set = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()

    markClassByGlyph, anchorsByBaseGlyph, _ = extract_mark_attachment_data(
        ttfont, lookup_index
    )

    out = {"codepoint": {}, "glyph": {}}

    # Reverse cmap: glyph → [codepoints]
    rev_cmap = {}
    for cp, gname in cmap.items():
        rev_cmap.setdefault(gname, []).append(cp)

    # Encoded bases
    for gname in ttfont.getGlyphOrder():
        cps = rev_cmap.get(gname, [])
        cps_in_base = [cp for cp in cps if cp in BASE_COVERAGE]
        if not cps_in_base:
            continue

        entry = build_glyph_entry(ttfont, glyph_set, anchorsByBaseGlyph, gname, style)

        for cp in cps_in_base:
            key = f"0x{cp:04X}"
            out["codepoint"][key] = entry

    # Unencoded small-cap bases
    for sc_name in base_small_capital_glyph:
        if sc_name not in glyph_set:
            continue

        entry = build_glyph_entry(ttfont, glyph_set, anchorsByBaseGlyph, sc_name, style)
        out["glyph"][sc_name] = entry

    return out
