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
    output_path = input_path.parent / f"{input_path.stem}-patch{input_path.suffix}"

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

    # ------------------------------------------------------------
    # Load curated human anchors
    # ------------------------------------------------------------
    human = ctx.get_human_anchors()
    base_anchors = human.get("bases", {})
    mark_anchors = human.get("marks", {})  # not used yet

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

        base_records = sub.BaseArray.BaseRecord
        base_glyphs = sub.BaseCoverage.glyphs

        # Patch each base glyph
        for i, glyph in enumerate(base_glyphs):

            # Find Unicode codepoint for this glyph
            cp = None
            for u, g in cmap.items():
                if g == glyph:
                    cp = u
                    break

            if cp is None:
                continue

            # If we have curated anchors for this codepoint, apply them
            if cp in base_anchors:
                class_map = base_anchors[cp]
                baserec = base_records[i]

                for classIndex, anchor in class_map.items():
                    x, y = anchor

                    # Replace or create the anchor
                    if baserec.BaseAnchor[classIndex] is None:
                        from fontTools.ttLib.tables.otTables import Anchor

                        new_anchor = Anchor()
                        new_anchor.XCoordinate = x
                        new_anchor.YCoordinate = y
                        new_anchor.Format = 1
                        baserec.BaseAnchor[classIndex] = new_anchor
                    else:
                        baserec.BaseAnchor[classIndex].XCoordinate = x
                        baserec.BaseAnchor[classIndex].YCoordinate = y

    # ------------------------------------------------------------
    # Save patched font (legacy behavior)
    # ------------------------------------------------------------
    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")
    