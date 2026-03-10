# font_patching.py — restored full patching behavior
"""
Patch Libertinus fonts using ONLY the human-curated anchors
stored in data/fontanchors_human/<font_key>.py.

This module uses FontContext as the canonical loader of all
font metadata, state, and curated anchor information.

This module is designed to be called from a wrapper script such as:
    from libertinus_analysis.font_patching import fontanchors_human
    patch_fontanchors_human("regular")
    patch_fontanchors_human("italic")
"""

import importlib
from fontTools.ttLib.tables.otTables import Anchor, BaseRecord
from .font_context import FontContext, FONTS

def load_human_anchors_runtime(font_key):
    """
    Load curated anchors from:
        data/fontanchors_human/<font_key>.py

    Returns {} if the module does not exist or fails to load.
    """
    module_name = f"data.fontanchors_human.{font_key}"

    try:
        module = __import__(module_name, fromlist=["anchors"])
    except Exception as e:
        print(f"[WARN] Could not import {module_name}: {e}")
        return {}

    anchors = getattr(module, "anchors", None)
    if anchors is None:
        print(f"[WARN] Module {module_name} has no 'anchors' dict")
        return {}

    return anchors

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
        font_key=None,      # <— prevents FontContext from loading curated anchors
        label=meta.get("label", font_key),
    )

    ttfont = ctx.ttfont
    cmap = ctx.cmap
    cmap_reverse = {g: u for u, g in cmap.items()}

    # Load curated anchors *now*, fresh
    human = load_human_anchors_runtime(font_key)
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

    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")