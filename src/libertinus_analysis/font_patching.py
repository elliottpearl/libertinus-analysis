"""
font_patching.py

Patch Libertinus fonts using anchor data from
data/fontdata/<font_key>.py.

This module is designed to be called from a wrapper script such as:

    from libertinus_analysis.font_patching import patch_libertinus_font
    patch_libertinus_font("regular")
    patch_libertinus_font("italic")

It uses the filename conventions and directory structure defined in
font_context.py (FONTS).
"""

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from libertinus_analysis.font_context import (
    FONTS,
    load_font_metrics,
)


def _get_markbasepos_lookup(font):
    """
    Return the MarkBasePos lookup and its subtable.

    This assumes the font uses a single MarkBasePos lookup for
    Latin/IPA (non-Hebrew) combining marks, and that it is the first 
    (or only) such MarkBasePos lookup in the GPOS table.

    If your fonts use a different structure, this function is the
    place to adapt it.
    """
    gpos = font["GPOS"].table
    for lookup in gpos.LookupList.Lookup:
        if lookup.LookupType == 4:  # MarkBasePos
            return lookup, lookup.SubTable[0]

    raise ValueError("No MarkBasePos lookup found in GPOS table.")


def _ensure_base_record(subtable, gname):
    """
    Ensure that gname appears in BaseCoverage and BaseArray.
    Return the BaseRecord for that glyph.
    """
    base_cov = subtable.BaseCoverage
    base_array = subtable.BaseArray

    if gname in base_cov.glyphs:
        idx = base_cov.glyphs.index(gname)
        return base_array.BaseRecord[idx]

    # Append new BaseRecord
    base_cov.glyphs.append(gname)

    br = otTables.BaseRecord()
    br.BaseAnchor = [None] * subtable.ClassCount
    base_array.BaseRecord.append(br)

    return br


def patch_libertinus_font(font_key):
    """
    Patch a Libertinus font using anchor data from
    data/fontdata/<font_key>.py.

    Parameters:
        font_key: str
            A key of FONTS, e.g. "regular", "italic", "semibold", "semibold_italic".

    The patched font is written to font file with "-patch" appended.
    """
    # Load anchor data for this font
    fontdata = load_font_metrics(font_key)
    anchors = fontdata.get("anchors", {})

    # Determine the font filename from the key
    font_info = FONTS[font_key]
    font_path = font_info["path"]

    # Construct output filename
    stem = font_path.stem
    ext = font_path.suffix
    out_path = font_path.with_name(f"{stem}-patch{ext}")

    font = TTFont(font_path)
    cmap = font.getBestCmap()

    lookup, subtable = _get_markbasepos_lookup(font)

    for class_id, table in anchors.items():
        for cp, (ax, ay) in table.items():

            # Skip codepoints not present in the font
            if cp not in cmap:
                continue

            gname = cmap[cp]
            br = _ensure_base_record(subtable, gname)

            anchor = otTables.Anchor()
            anchor.Format = 1
            anchor.XCoordinate = ax
            anchor.YCoordinate = ay
            anchor.AnchorPoint = None

            br.BaseAnchor[class_id] = anchor

    font.save(out_path)
    font.close()

    print(f"Patched font saved to: {out_path}")
