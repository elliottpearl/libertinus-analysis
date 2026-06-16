# font_patching_anchors.py
"""
Anchor-patching stage of the Libertinus patching pipeline.

Loads human-curated anchors lazily based on font_key.

Supports:
    - bases (Unicode-keyed)
    - marks (Unicode-keyed)
    - bases_by_name (glyph-name-keyed)
    - marks_by_name (glyph-name-keyed)
"""

from fontTools.ttLib.tables.otTables import Anchor, BaseRecord


# ------------------------------------------------------------
# Lazy loader for human-curated anchor modules
# ------------------------------------------------------------

def load_human_anchors(font_key: str):
    """
    Dynamically import data.fontanchors_human.<font_key>
    and return its `anchors` dict.
    """
    module_name = f"data.fontanchors_human.{font_key}"
    mod = __import__(module_name, fromlist=["anchors"])
    return mod.anchors


# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def patch_anchors_human(ttfont, font_key, lookup_index, cmap, cmap_reverse):
    """
    Patch a Libertinus font using ONLY the human-curated anchors.

    Supports:
        - bases (Unicode-keyed)
        - marks (Unicode-keyed)
        - bases_by_name (glyph-name-keyed)
        - marks_by_name (glyph-name-keyed)

    Existing anchors are overwritten, never deleted.
    Missing BaseRecords and MarkRecords are created as needed.
    """

    # Load curated anchors lazily
    human = load_human_anchors(font_key)

    base_cp       = human.get("bases", {})
    mark_cp       = human.get("marks", {})
    base_by_name  = human.get("bases_by_name", {})
    mark_by_name  = human.get("marks_by_name", {})

    # Access GPOS lookup
    gpos = ttfont["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    # ------------------------------------------------------------
    # Patch MarkToBase subtables
    # ------------------------------------------------------------
    for sub in lookup.SubTable:
        if sub.LookupType != 4:
            continue

        base_cov   = sub.BaseCoverage
        base_array = sub.BaseArray
        class_count = sub.ClassCount

        # ========================================================
        # 1. Patch base anchors (Unicode-keyed)
        # ========================================================
        for cp, class_map in base_cp.items():
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

            # Ensure BaseAnchor list matches ClassCount
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

        # ========================================================
        # 2. Patch mark anchors (Unicode-keyed)
        # ========================================================
        mark_records = sub.MarkArray.MarkRecord
        mark_glyphs  = sub.MarkCoverage.glyphs

        for i, glyph in enumerate(mark_glyphs):
            cp = cmap_reverse.get(glyph)
            if cp is None:
                continue

            if cp in mark_cp:
                class_map = mark_cp[cp]
                markrec = mark_records[i]
                mark_class = markrec.Class

                if mark_class in class_map:
                    x, y = class_map[mark_class]
                    anchor = markrec.MarkAnchor
                    anchor.XCoordinate = x
                    anchor.YCoordinate = y

        # ========================================================
        # 3. Patch base anchors (glyph-name-keyed)
        # ========================================================
        for glyph_name, class_map in base_by_name.items():

            # If glyph not in BaseCoverage, add it
            if glyph_name in base_cov.glyphs:
                idx = base_cov.glyphs.index(glyph_name)
                baserec = base_array.BaseRecord[idx]
            else:
                base_cov.glyphs.append(glyph_name)
                baserec = BaseRecord()
                baserec.BaseAnchor = [None] * class_count
                base_array.BaseRecord.append(baserec)

            # Ensure BaseAnchor list matches ClassCount
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

        # ========================================================
        # 4. Patch mark anchors (glyph-name-keyed)
        # ========================================================
        mark_records = sub.MarkArray.MarkRecord
        mark_glyphs  = sub.MarkCoverage.glyphs

        for glyph_name, class_map in mark_by_name.items():

            # If glyph already in MarkCoverage, patch it
            if glyph_name in mark_glyphs:
                idx = mark_glyphs.index(glyph_name)
                markrec = mark_records[idx]
                mark_class = markrec.Class

                if mark_class in class_map:
                    x, y = class_map[mark_class]
                    anchor = markrec.MarkAnchor
                    anchor.XCoordinate = x
                    anchor.YCoordinate = y

            else:
                # Glyph not in MarkCoverage → create a new MarkRecord
                # NOTE: This preserves your legacy behavior: we do not
                #       modify ClassCount or MarkClass definitions.
                #       We simply assign class 0.
                from fontTools.ttLib.tables.otTables import MarkRecord

                mark_glyphs.append(glyph_name)

                newrec = MarkRecord()
                newrec.Class = 0  # default class
                newrec.MarkAnchor = Anchor()
                newrec.MarkAnchor.Format = 1

                mark_records.append(newrec)

                # If class 0 is defined in class_map, apply it
                if 0 in class_map:
                    x, y = class_map[0]
                    newrec.MarkAnchor.XCoordinate = x
                    newrec.MarkAnchor.YCoordinate = y
