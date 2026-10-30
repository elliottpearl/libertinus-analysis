# font_patching_sortcoverage.py
"""
Coverage-sorting stage of the Libertinus patching pipeline (stage 10).

The anchor stages append new bases and marks to the end of the mark-to-base
coverage tables. OpenType requires a Coverage table in glyph-ID order, so
fontTools warns "GSUB/GPOS Coverage is not sorted by glyph ids." when it
compiles one that is not. (It still writes a working font, but the warning
recurs every time the patched font is loaded and recompiled.)

This stage sorts BaseCoverage and MarkCoverage of the style's mark-to-base
lookup by glyph ID and reorders BaseArray and MarkArray with them, so that
every glyph keeps its own record.
"""

def _sort_parallel(ttfont, coverage, records):
    """
    Sort coverage.glyphs by glyph ID and reorder records (a list parallel to
    it) in place. Return True if the order changed.
    """
    glyphs = coverage.glyphs
    ids = ttfont.getGlyphIDMany(glyphs)
    order = sorted(range(len(glyphs)), key=lambda i: ids[i])
    if order == list(range(len(glyphs))):
        return False
    coverage.glyphs = [glyphs[i] for i in order]
    records[:] = [records[i] for i in order]
    return True

def sort_mark_to_base_coverage(ttfont, lookup_index):
    """
    Sort the base and mark coverage of every MarkToBase subtable in the
    lookup. Returns: list of report lines.
    """
    report = []
    lookup = ttfont["GPOS"].table.LookupList.Lookup[lookup_index]

    for n, sub in enumerate(lookup.SubTable):
        if sub.LookupType != 4:
            continue

        if _sort_parallel(ttfont, sub.BaseCoverage, sub.BaseArray.BaseRecord):
            report.append(f"lookup {lookup_index} subtable {n}: sorted BaseCoverage ({len(sub.BaseCoverage.glyphs)} glyphs)")
        sub.BaseArray.BaseCount = len(sub.BaseArray.BaseRecord)

        if _sort_parallel(ttfont, sub.MarkCoverage, sub.MarkArray.MarkRecord):
            report.append(f"lookup {lookup_index} subtable {n}: sorted MarkCoverage ({len(sub.MarkCoverage.glyphs)} glyphs)")
        sub.MarkArray.MarkCount = len(sub.MarkArray.MarkRecord)

    return report
