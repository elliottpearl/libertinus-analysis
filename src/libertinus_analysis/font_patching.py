"""
font_patching.py

Patch Libertinus fonts using anchor data from
data/fontdata/libertinus_regular.py.

This module is designed to be called from a wrapper script such as:

    from libertinus_analysis.font_patching import patch_libertinus_font
    patch_libertinus_font("LibertinusSerif-Regular.otf")

It uses the filename conventions and directory structure defined in
font_context.py (FONTS_DIR).
"""

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from libertinus_analysis.font_context import FONTS_DIR
from data.fontdata import libertinus_regular


def _load_anchor_data():
    """
    Return the anchor dict from data/fontdata/libertinus_regular.py.
    """
    return libertinus_regular.fontdata["anchors"]


def _get_markbasepos_lookup(font):
    """
    Return the MarkBasePos lookup and its subtable.

    This assumes the font uses a single MarkBasePos lookup for
    superscript consonants, and that it is the first (or only)
    MarkBasePos lookup in the GPOS table.

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


def patch_libertinus_font(font_filename, out_filename=None):
    """
    Patch a Libertinus font using anchor data from libertinus_regular.py.

    Parameters:
        font_filename: str
            Filename inside FONTS_DIR, e.g. "LibertinusSerif-Regular.otf"

        out_filename: str or None
            Output filename inside FONTS_DIR. If None, "-patch" is appended.

    The patched font is written to FONTS_DIR/out_filename.
    """
    font_path = FONTS_DIR / font_filename
    if out_filename is None:
        stem = font_filename.rsplit(".", 1)[0]
        ext = font_filename.rsplit(".", 1)[1]
        out_filename = f"{stem}-patch.{ext}"

    out_path = FONTS_DIR / out_filename

    font = TTFont(font_path)
    cmap = font.getBestCmap()

    anchors = _load_anchor_data()
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