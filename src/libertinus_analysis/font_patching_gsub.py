# font_patching_gsub.py
"""
GSUB-patching stage of the patching pipeline.

Rebuilds GSUB from a human-curated .fea file, while preserving GPOS.
"""

from fontTools.feaLib.builder import Builder
from fontTools.ttLib.tables import otTables


def _merge_mark_glyph_sets(ttfont, built_gdef):
    """
    Carry the mark glyph sets of the .fea (UseMarkFilteringSet, e.g. ccmp's
    dot removal) into the restored GDEF. The builder numbers its sets from 0,
    and the original GDEF has sets of its own (regular's set 0 is U+0305
    U+0332), so each built set is appended (or matched to an identical set)
    and the new GSUB's MarkFilteringSet indices are renumbered (2026-11-27).
    GPOS is the original's and keeps the original numbering.
    """
    built = getattr(built_gdef.table, "MarkGlyphSetsDef", None) if built_gdef is not None else None
    if built is None or not built.Coverage:
        return
    gdef = ttfont["GDEF"].table
    if getattr(gdef, "MarkGlyphSetsDef", None) is None:
        gdef.MarkGlyphSetsDef = otTables.MarkGlyphSetsDef()
        gdef.MarkGlyphSetsDef.MarkSetTableFormat = 1
        gdef.MarkGlyphSetsDef.Coverage = []
        gdef.Version = max(gdef.Version, 0x00010002)
    sets = gdef.MarkGlyphSetsDef.Coverage
    remap = {}
    for i, cov in enumerate(built.Coverage):
        glyphs = set(cov.glyphs)
        match = next((k for k, c in enumerate(sets) if set(c.glyphs) == glyphs), None)
        if match is None:
            sets.append(cov)
            match = len(sets) - 1
        remap[i] = match
    gdef.MarkGlyphSetsDef.MarkSetCount = len(sets)
    for lookup in ttfont["GSUB"].table.LookupList.Lookup:
        if lookup.LookupFlag & 0x0010:
            lookup.MarkFilteringSet = remap[lookup.MarkFilteringSet]

def patch_gsub_ccmp(ttfont, font_key: str) -> None:
    """
    Patch GSUB using the human-curated ccmp.fea file for the given font_key.

    This preserves the original behavior:
    - Save original GPOS and GDEF
    - Run feaLib Builder on ccmp.fea (which rebuilds GSUB and nukes GPOS and GDEF)
    - Restore original GPOS and GDEF
    """

    ccmp_fea_path = f"data/fea/{font_key}/ccmp.fea"

    # Save original GPOS so Builder can't destroy it
    original_gpos = ttfont["GPOS"]
    # ... nor GDEF (glyph classes and mark glyph sets, which GPOS lookups use)
    original_gdef = ttfont["GDEF"] if "GDEF" in ttfont else None

    try:
        builder = Builder(ttfont, ccmp_fea_path)
        builder.build()  # This rebuilds GSUB *and nukes GPOS*
        built_gdef = ttfont["GDEF"] if "GDEF" in ttfont else None
        # Restore original GPOS
        ttfont["GPOS"] = original_gpos
        if original_gdef is not None:
            ttfont["GDEF"] = original_gdef
            _merge_mark_glyph_sets(ttfont, built_gdef)
        print(f"Applied GSUB features from {ccmp_fea_path}")
    except Exception as e:
        print(f"WARNING: Failed to apply GSUB features from {ccmp_fea_path}: {e}")
