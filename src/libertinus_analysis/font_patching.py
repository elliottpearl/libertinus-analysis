# font_patching.py

from fontTools.ttLib import TTFont
from .font_context import FontContext, FONTS


def patch_fontanchors_human(font_key):
    """
    Patch a Libertinus font using ONLY the human-curated anchors in
    data/fontanchors_human/<font_key>.py.

    This uses the EXACT legacy output filename convention:
        <stem>-patch<suffix>
    written to the same directory as the input font.
    """

    # ------------------------------------------------------------
    # Load font metadata
    # ------------------------------------------------------------
    font_info = FONTS[font_key]
    input_path = font_info["path"]
    lookup_index = font_info["lookup_index"]

    # EXACT legacy behavior:
    #   LibertinusSerif-Regular.otf → LibertinusSerif-Regular-patch.otf
    output_path = input_path.with_name(f"{input_path.stem}-patch{input_path.suffix}")

    # ------------------------------------------------------------
    # Load font + context
    # ------------------------------------------------------------
    ctx = FontContext.from_path(
        path=input_path,
        lookup_index=lookup_index,
        font_key=font_key,
        label=f"{font_key} (patched)",
    )

    ttfont = ctx.ttfont
    cmap = ctx.cmap

    # Reverse cmap: glyphName → codepoint
    cmap_reverse = {g: u for u, g in cmap.items()}

    # ------------------------------------------------------------
    # Load curated human anchors
    # ------------------------------------------------------------
    human = ctx.get_human_anchors()
    base_anchors = human.get("bases", {})
    mark_anchors = human.get("marks", {})

    # ------------------------------------------------------------
    # Access the GPOS lookup we are patching
    # ------------------------------------------------------------
    gpos = ttfont["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    # ------------------------------------------------------------
    # Patch MarkToBase subtables
    # ------------------------------------------------------------
    for sub in lookup.SubTable:
        if sub.LookupType != 4:  # MarkToBase
            continue

        # ========================================================
        # 1. PATCH BASE ANCHORS
        # ========================================================
        base_records = sub.BaseArray.BaseRecord
        base_glyphs = sub.BaseCoverage.glyphs

        for i, glyph in enumerate(base_glyphs):

            cp = cmap_reverse.get(glyph)
            if cp is None:
                continue

            if cp in base_anchors:
                class_map = base_anchors[cp]
                baserec = base_records[i]

                for classIndex, (x, y) in class_map.items():
                    anchor = baserec.BaseAnchor[classIndex]
                    if anchor is None:
                        from fontTools.ttLib.tables.otTables import Anchor
                        anchor = Anchor()
                        anchor.Format = 1
                        baserec.BaseAnchor[classIndex] = anchor

                    anchor.XCoordinate = x
                    anchor.YCoordinate = y

        # ========================================================
        # 2. PATCH MARK ANCHORS
        # ========================================================
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

                # Only patch if we have data for this mark class
                if mark_class in class_map:
                    x, y = class_map[mark_class]

                    anchor = markrec.MarkAnchor
                    anchor.XCoordinate = x
                    anchor.YCoordinate = y

    # ------------------------------------------------------------
    # Save patched font (legacy behavior)
    # ------------------------------------------------------------
    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")
    