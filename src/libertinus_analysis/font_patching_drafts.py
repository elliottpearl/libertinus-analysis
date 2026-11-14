# font_patching_drafts.py
"""
Stage 2 of the patch: add the approved drafts of the letters a style lacks
(2026-11-14).

The drafts are built by missing_glyphs.py (run_missing_glyphs_sheet.py) from
the style's own letters, reviewed on tex/missing_glyphs_test_sheet.pdf, and
their outlines, with overlaps merged as font generation merges them, are
written to data/draft_glyphs/{style}.json once approved. This stage only
reads that file: it adds each glyph (outline, advance, cmap, GDEF base
class) where the font lacks the character, before the anchor stages, so that
stages 6-8 give the drafts their anchors as they would the designer's
letters, and stage 10 puts the draft capitals in @capitals (data/fea/{style}/ccmp.fea).

The recipes read the patched fonts but take a letter as missing from the
original fonts' coverage, so rebuilding the drafts after a patch that
contains them gives the same outlines.
"""

import json
from pathlib import Path

from fontTools.pens.t2CharStringPen import T2CharStringPen

DRAFTS_DIR = Path("data/draft_glyphs")


def add_draft_glyphs(ttfont, font_key):
    """Add the approved drafts listed for this style. Returns report lines."""
    path = DRAFTS_DIR / f"{font_key}.json"
    if not path.exists():
        return [f"no approved drafts ({path})"]
    drafts = json.loads(path.read_text(encoding="utf-8"))
    cmap = ttfont.getBestCmap()
    top = ttfont["CFF "].cff.topDictIndex[0]
    charstrings, private = top.CharStrings, top.Private
    report = []
    for glyph_name, entry in drafts.items():
        cp, advance = entry["unicode"], entry["advance"]
        if cp in cmap:
            report.append(f"U+{cp:04X} {glyph_name}: already in the font; draft not added")
            continue
        width = None if advance == private.defaultWidthX else advance - private.nominalWidthX
        pen = T2CharStringPen(width, None)
        xs = []
        for op, pts in entry["outline"]:
            pts = [tuple(p) for p in pts]
            xs += [p[0] for p in pts]
            getattr(pen, op)(*pts)
        charstring = pen.getCharString(private=private, globalSubrs=top.GlobalSubrs)
        if glyph_name in charstrings.charStrings:
            # A glyph of that name with no Unicode (semibold's uni1EFB): replaced.
            charstrings[glyph_name] = charstring
        else:
            order = ttfont.getGlyphOrder()
            order.append(glyph_name)
            ttfont.setGlyphOrder(order)
            if top.charset is not order and glyph_name not in top.charset:
                top.charset.append(glyph_name)
            charstrings.charStrings[glyph_name] = len(charstrings.charStringsIndex)
            charstrings.charStringsIndex.append(charstring)
        ttfont["hmtx"].metrics[glyph_name] = (advance, round(min(xs)) if xs else 0)
        gdef = ttfont["GDEF"].table
        if gdef.GlyphClassDef is not None:
            gdef.GlyphClassDef.classDefs[glyph_name] = 1   # base
        for table in ttfont["cmap"].tables:
            if table.isUnicode():
                table.cmap[cp] = glyph_name
        report.append(f"U+{cp:04X} {glyph_name}: approved draft added, advance {advance}")
    return report
