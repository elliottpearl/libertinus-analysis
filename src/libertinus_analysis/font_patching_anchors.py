# font_patching_anchors.py
"""
Anchor-patching stage of the Libertinus patching pipeline.

Uses human-curated anchors to set or overwrite anchors for:
    - bases (Unicode-keyed)
    - marks (Unicode-keyed)
    - bases_by_name (glyph-name-keyed)
    - marks_by_name (glyph-name-keyed)

Behavior:
    - Existing anchors are overwritten, never deleted.
    - Missing BaseRecords and MarkRecords are created as needed.
    - For marks, the MarkRecord.Class is set to the curated class
      (one class per mark, per OpenType/GPOS).
"""

from fontTools.ttLib.tables.otTables import Anchor, BaseRecord, MarkRecord


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
# Helpers
# ------------------------------------------------------------

def ensure_base_record(sub, glyph_name):
    """
    Ensure glyph_name exists in BaseCoverage/BaseArray and return its BaseRecord.
    """
    base_cov = sub.BaseCoverage
    base_array = sub.BaseArray
    class_count = sub.ClassCount

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

    return baserec


def ensure_mark_record(sub, glyph_name):
    """
    Ensure glyph_name exists in MarkCoverage/MarkArray and return its MarkRecord.
    """
    mark_cov = sub.MarkCoverage
    mark_array = sub.MarkArray

    if glyph_name in mark_cov.glyphs:
        idx = mark_cov.glyphs.index(glyph_name)
        return mark_array.MarkRecord[idx]

    # Create new MarkRecord with default class 0
    mark_cov.glyphs.append(glyph_name)
    newrec = MarkRecord()
    newrec.Class = 0
    newrec.MarkAnchor = Anchor()
    newrec.MarkAnchor.Format = 1
    mark_array.MarkRecord.append(newrec)
    return newrec


# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def patch_anchors_human(ttfont, font_key, lookup_index, cmap, cmap_reverse):
    """
    Patch a Libertinus font using ONLY the human-curated anchors.

    Existing anchors are overwritten, never deleted.
    Missing BaseRecords and MarkRecords are created as needed.
    For marks, the MarkRecord.Class is set to the curated class.
    """

    human = load_human_anchors(font_key)

    base_cp       = human.get("bases", {})
    mark_cp       = human.get("marks", {})
    base_by_name  = human.get("bases_by_name", {})
    mark_by_name  = human.get("marks_by_name", {})

    gpos = ttfont["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    for sub in lookup.SubTable:
        if sub.LookupType != 4:
            continue  # only MarkToBase

        # --------------------------------------------------------
        # 1. Patch base anchors (Unicode-keyed)
        # --------------------------------------------------------
        for cp, class_map in base_cp.items():
            if cp not in cmap:
                continue

            glyph_name = cmap[cp]
            baserec = ensure_base_record(sub, glyph_name)

            for classIndex, (x, y) in class_map.items():
                anchor = baserec.BaseAnchor[classIndex]
                if anchor is None:
                    anchor = Anchor()
                    anchor.Format = 1
                    baserec.BaseAnchor[classIndex] = anchor

                anchor.XCoordinate = x
                anchor.YCoordinate = y

        # --------------------------------------------------------
        # 2. Patch mark anchors (Unicode-keyed)
        # --------------------------------------------------------
        for cp, class_map in mark_cp.items():
            if cp not in cmap:
                continue

            glyph_name = cmap[cp]
            markrec = ensure_mark_record(sub, glyph_name)

            # Assume one curated class per glyph; use the first key.
            curated_classes = list(class_map.keys())
            if not curated_classes:
                continue
            curated_class = curated_classes[0]

            # Overwrite MarkRecord.Class with curated class.
            markrec.Class = curated_class

            x, y = class_map[curated_class]
            anchor = markrec.MarkAnchor
            anchor.XCoordinate = x
            anchor.YCoordinate = y

        # --------------------------------------------------------
        # 3. Patch base anchors (glyph-name-keyed)
        # --------------------------------------------------------
        for glyph_name, class_map in base_by_name.items():
            baserec = ensure_base_record(sub, glyph_name)

            for classIndex, (x, y) in class_map.items():
                anchor = baserec.BaseAnchor[classIndex]
                if anchor is None:
                    anchor = Anchor()
                    anchor.Format = 1
                    baserec.BaseAnchor[classIndex] = anchor

                anchor.XCoordinate = x
                anchor.YCoordinate = y

        # --------------------------------------------------------
        # 4. Patch mark anchors (glyph-name-keyed)
        # --------------------------------------------------------
        for glyph_name, class_map in mark_by_name.items():
            markrec = ensure_mark_record(sub, glyph_name)

            # Again, assume one curated class per glyph; use the first key.
            curated_classes = list(class_map.keys())
            if not curated_classes:
                continue
            curated_class = curated_classes[0]

            # Overwrite MarkRecord.Class with curated class.
            markrec.Class = curated_class

            x, y = class_map[curated_class]
            anchor = markrec.MarkAnchor
            anchor.XCoordinate = x
            anchor.YCoordinate = y
