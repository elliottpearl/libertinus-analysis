# font_patching_mergeclasses.py
"""
Anchor-class merge stage of the Libertinus patching pipeline.

Semibold has a second above class, the designer's "top_punkt" (class 1 of
its mark-to-base lookup): the dot above, diaeresis, ring, hook above, the
comma-above family, U+0351, U+0357, U+0363 and hookabovecomb.cap. It places
nothing differently from "above" (class 0): each top_punkt base anchor is the
above anchor moved down (96 on lowercase, 83 on capitals), and each top_punkt
mark anchor is about 96 lower on its outline. But only 24 bases have it, so in
the original font the dot-like marks are unattached on most letters. The
other styles have no top_punkt (semibold italic declares it but it is empty).

This stage moves those marks into class 0, their anchor raised by 96, and
removes the top_punkt base anchors. A base with top_punkt but no above anchor
(G) gets one, moved up by its case's shift. U+0315 (comma above right) stays
in class 1, which is then the above-right class as in the other styles, with
no base anchors yet.

Run it before the stages that copy or set mark anchors, so that they all see
one above class.
"""

from fontTools.ttLib.tables.otTables import Anchor

# font_key -> merge of a base/mark class into another.
MERGES = {
    "semibold": {
        "from": 1,
        "into": 0,
        "mark_dy": 96,                       # mark anchor raise
        "base_dy": {"upper": 83, "lower": 96},  # promoting a base anchor
        "keep": {"uni0315"},                 # stays in class 1 (above right)
    },
}


def merge_anchor_classes(ttfont, font_key, lookup_index):
    """Merge one anchor class into another per MERGES. Returns a report."""
    merge = MERGES.get(font_key)
    if merge is None:
        return []

    src, dst = merge["from"], merge["into"]
    cmap_reverse = {g: u for u, g in ttfont.getBestCmap().items()}
    lookup = ttfont["GPOS"].table.LookupList.Lookup[lookup_index]

    moved, promoted, dropped = [], [], 0
    for sub in lookup.SubTable:
        if sub.LookupType != 4:
            continue  # only MarkToBase

        for glyph_name, record in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
            if record.Class != src or glyph_name in merge["keep"]:
                continue
            record.Class = dst
            record.MarkAnchor.YCoordinate += merge["mark_dy"]
            moved.append(glyph_name)

        for glyph_name, record in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
            anchor = record.BaseAnchor[src]
            if anchor is None:
                continue
            if record.BaseAnchor[dst] is None:
                cp = cmap_reverse.get(glyph_name)
                case = "upper" if cp is not None and chr(cp).isupper() else "lower"
                new = Anchor()
                new.Format = 1
                new.XCoordinate = anchor.XCoordinate
                new.YCoordinate = anchor.YCoordinate + merge["base_dy"][case]
                record.BaseAnchor[dst] = new
                promoted.append(f"{glyph_name} ({new.XCoordinate}, {new.YCoordinate})")
            record.BaseAnchor[src] = None
            dropped += 1

    return [
        f"class {src} -> {dst}: {len(moved)} marks moved ({', '.join(moved)}), anchor y +{merge['mark_dy']}",
        f"class {src} base anchors removed: {dropped}; promoted to class {dst}: {', '.join(promoted) or 'none'}",
    ]
