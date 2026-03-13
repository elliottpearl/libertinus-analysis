# font_patching.py — restored full patching behavior
"""
Patch Libertinus fonts using ONLY the human-curated anchors
stored in data/fontanchors_human/<font_key>.py.

This module is designed to be called from a wrapper script such as:
    from libertinus_analysis.font_patching import patch_fontanchors_human
    patch_fontanchors_human("regular")
    patch_fontanchors_human("italic")
"""

from fontTools.feaLib.builder import Builder
from fontTools.ttLib.tables.otTables import Anchor, BaseRecord
from .font_context import FontContext, FONTS

# Static imports of all curated anchor modules
from data.fontanchors_human import regular
from data.fontanchors_human import italic
from data.fontanchors_human import semibold
from data.fontanchors_human import semibold_italic

# Map font_key → anchors dict
HUMAN_ANCHORS = {
    "regular": regular.anchors,
    "italic": italic.anchors,
    "semibold": semibold.anchors,
    "semibold_italic": semibold_italic.anchors,
}


def patch_fontanchors_human(font_key):
    """
    Patch a Libertinus font using ONLY the human-curated anchors.
    - All curated anchors are written
    - Missing BaseRecords are created
    - Missing BaseCoverage entries are added
    - BaseAnchor lists are padded to ClassCount
    - Existing anchors are overwritten, never deleted
    """

    meta = FONTS[font_key]
    input_path = meta["path"]
    lookup_index = meta["lookup_index"]

    output_path = input_path.with_name(f"{input_path.stem}-patch{input_path.suffix}")

    # Load font context WITHOUT curated anchors
    ctx = FontContext.from_path(
        path=input_path,
        lookup_index=lookup_index,
        font_key=None,      # prevents FontContext from loading curated anchors
        label=meta.get("label", font_key),
    )

    ttfont = ctx.ttfont
    cmap = ctx.cmap
    cmap_reverse = {g: u for u, g in cmap.items()}

    # Load curated anchors directly from static mapping
    human = HUMAN_ANCHORS.get(font_key, {})
    base_anchors = human.get("bases", {})
    mark_anchors = human.get("marks", {})

    # Access GPOS lookup
    gpos = ttfont["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    # Patch MarkToBase subtables
    for sub in lookup.SubTable:
        if sub.LookupType != 4:
            continue

        base_cov = sub.BaseCoverage
        base_array = sub.BaseArray
        class_count = sub.ClassCount

        # -------------------------
        # 1. Patch base anchors
        # -------------------------
        for cp, class_map in base_anchors.items():
            if cp not in cmap:
                continue

            glyph = cmap[cp]

            if glyph in base_cov.glyphs:
                idx = base_cov.glyphs.index(glyph)
                baserec = base_array.BaseRecord[idx]
            else:
                base_cov.glyphs.append(glyph)
                baserec = BaseRecord()
                baserec.BaseAnchor = [None] * class_count
                base_array.BaseRecord.append(baserec)

            while len(baserec.BaseAnchor) < class_count:
                baserec.BaseAnchor.append(None)

            for classIndex, (x, y) in class_map.items():
                anchor = baserec.BaseAnchor[classIndex]
                if anchor is None:
                    anchor = Anchor()
                    anchor.Format = 1
                    baserec.BaseAnchor[classIndex] = anchor

                anchor.XCoordinate = x
                anchor.YCoordinate = y

        # -------------------------
        # 2. Patch mark anchors
        # -------------------------
        mark_records = sub.MarkArray.MarkRecord
        mark_glyphs = sub.MarkCoverage.glyphs

        for i, glyph in enumerate(mark_glyphs):
            cp = cmap_reverse.get(glyph)
            if cp is None:
                continue

            if cp in mark_anchors:
                class_map = mark_anchors[cp]
                markrec = mark_records[i]
                mark_class = markrec.Class

                if mark_class in class_map:
                    x, y = class_map[mark_class]
                    anchor = markrec.MarkAnchor
                    anchor.XCoordinate = x
                    anchor.YCoordinate = y

    # ------------------------------------------------------------
    # 3. Patch GSUB using human-curated .fea file
    # ------------------------------------------------------------
    ccmp_fea_path = f"data/fea/{font_key}/ccmp.fea"

    # Save original GPOS so Builder can't destroy it
    original_gpos = ttfont["GPOS"]

    try:
        builder = Builder(ttfont, ccmp_fea_path)
        builder.build()  # This rebuilds GSUB *and nukes GPOS*
        # Restore original GPOS
        ttfont["GPOS"] = original_gpos
        print(f"Applied GSUB features from {ccmp_fea_path}")
    except Exception as e:
        print(f"WARNING: Failed to apply GSUB features from {ccmp_fea_path}: {e}")

    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")
    