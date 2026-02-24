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

def patch_libertinus_font(font_key):
    fontdata = load_font_metrics(font_key)
    anchors = fontdata.get("anchors", {})

    font_info = FONTS[font_key]
    font_path = font_info["path"]

    stem = font_path.stem
    ext = font_path.suffix
    out_path = font_path.with_name(f"{stem}-patch{ext}")

    font = TTFont(font_path)
    gpos = font["GPOS"].table
    cmap = font["cmap"].getcmap(3, 1).cmap

    lookup_index = font_info["lookup_index"]
    
    lookup = gpos.LookupList.Lookup[lookup_index]
    subtable = lookup.SubTable[0]  # MarkBasePos Format 1

    base_cov = subtable.BaseCoverage
    base_array = subtable.BaseArray
    class_count = subtable.ClassCount

    # --- Patch anchors ---
    for class_id, table in anchors.items():
        for cp, (ax, ay) in table.items():

            # Skip codepoints not in cmap
            if cp not in cmap:
                print("Skipping missing codepoint:", hex(cp))
                continue

            gname = cmap[cp]

            # --- Ensure BaseRecord exists ---
            if gname in base_cov.glyphs:
                idx = base_cov.glyphs.index(gname)
                br = base_array.BaseRecord[idx]
            else:
                # Add new glyph to BaseCoverage
                base_cov.glyphs.append(gname)

                # Create a new BaseRecord with empty anchors
                br = otTables.BaseRecord()
                br.BaseAnchor = [None] * class_count

                # Append to BaseArray
                base_array.BaseRecord.append(br)

            # --- Normalize BaseAnchor list to class_count ---
            if br.BaseAnchor is None:
                br.BaseAnchor = [None] * class_count
            else:
                # Pad with None until we have class_count entries
                while len(br.BaseAnchor) < class_count:
                    br.BaseAnchor.append(None)

            # --- Create anchor ---
            anchor = otTables.Anchor()
            anchor.Format = 1
            anchor.XCoordinate = ax
            anchor.YCoordinate = ay
            anchor.AnchorPoint = None

            # --- Assign anchor to correct class slot ---
            br.BaseAnchor[class_id] = anchor

    # --- Save patched font ---
    font.save(out_path)
    font.close()

    print(f"Patched font saved to: {out_path}")
