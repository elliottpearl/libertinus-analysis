# fontmetrics_extractor.py
#
# Extract bbox, anchors, horizontal metrics (width, lsb, rsb),
# and semantic tags for:
#   - all BASE_COVERAGE codepoints (encoded glyphs)
#   - MARK_ABOVE and MARK_BELOW
#   - all base_small_capital_glyph names (unencoded small-cap bases)
#   - mark_small_capital_glyph and mark_superscript_glyph custom glyuphs
#
# Writes JSON to data/fontmetrics/<font_key>.json.

import json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

from .font_context import extract_mark_attachment_data
from .font_context import FONTS

from data.ipa.ipa_unicode import (
    BASE_COVERAGE,
    MARK_ABOVE,
    MARK_BELOW,
    base_small_capital_glyph,
    mark_small_capital_glyph,
    mark_superscript_glyph,
)
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

    # Legacy compatibility
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
# Geometry helpers
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
# Build JSON entry for a single glyph
# ------------------------------------------------------------

def build_glyph_entry(ttfont, glyph_set, anchorsByGlyph, gname):
    bbox = get_glyph_bbox(glyph_set, gname)

    anchors = anchorsByGlyph.get(gname, {})
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
# Main extraction entry point
# ------------------------------------------------------------

def extract_fontmetrics(font_key, lookup_index):
    font_path = FONTS[font_key]["path"]

    ttfont = TTFont(font_path)
    glyph_set = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()

    # NEW: unified anchor model
    anchorsByGlyph, _ = extract_mark_attachment_data(ttfont, lookup_index)

    out = {"codepoint": {}, "glyph": {}}

    # Reverse cmap: glyph → list of codepoints
    rev_cmap = {}
    for cp, gname in cmap.items():
        rev_cmap.setdefault(gname, []).append(cp)

    # ------------------------------------------------------------
    # Extract metrics for encoded glyphs (by codepoint)
    # ------------------------------------------------------------

    CP = BASE_COVERAGE + MARK_BELOW + MARK_ABOVE

    for gname in ttfont.getGlyphOrder():
        cps = rev_cmap.get(gname, [])
        cps_in_scope = [cp for cp in cps if cp in CP]
        if not cps_in_scope:
            continue

        entry = build_glyph_entry(ttfont, glyph_set, anchorsByGlyph, gname)

        for cp in cps_in_scope:
            key = f"0x{cp:04X}"
            out["codepoint"][key] = entry

    # ------------------------------------------------------------
    # Extract metrics for unencoded glyphs (by glyph name)
    # ------------------------------------------------------------

    glyph_names = (
        base_small_capital_glyph
        + mark_small_capital_glyph
        + mark_superscript_glyph
    )

    for sc_name in glyph_names:
        if sc_name not in glyph_set:
            continue

        entry = build_glyph_entry(ttfont, glyph_set, anchorsByGlyph, sc_name)
        out["glyph"][sc_name] = entry

    return out
