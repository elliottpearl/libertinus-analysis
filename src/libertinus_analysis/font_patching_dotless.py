# font_patching_dotless.py
"""
Dotless forms of the precomposed soft-dotted letters (2026-11-27).

HarfBuzz composes i + U+0323 into ị (U+1ECB), i + U+0330 into ḭ (U+1E2D) and
i + U+0328 into į (U+012F) before GSUB runs, wherever the font has the
precomposed glyph. An above mark that follows (ị́ in Igbo) then meets a glyph
with its own dot, which ccmp's dot-removal rule (@dotted -> @dotless) did not
know. ʝ (U+029D) and Cyrillic і ј (U+0456, U+0458) have no decomposition
but are Soft_Dotted too. Each gets an
unencoded dotless form, which ccmp substitutes before an above mark, as Noto
Serif does (idotbelowdotless).

Stage 2 (add_dotless_glyphs): the dotless form is the designer's precomposed
glyph with the dot contour removed (the contour whose bottom is above
DOT_MIN_Y), at the same advance, so the mark below keeps the designer's
placement.

Anchors: above is inherited from ı (ȷ for ʝ and ј) in stage 8 (derived_by_name in
data/derived_letters.py). The other classes (below, ogonek/hook, ...) are
the dotted glyph's, copied after stage 9 (copy_dotless_anchors): the dot
removal changes nothing under the x-height.
"""

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen

from .font_patching_addmarks import _set_outline
from .font_patching_redraw import _replace_outline
from .font_patching_inherit import (
    find_mark_to_base_subtables,
    get_base_record_for_glyph,
    ensure_base_record_for_glyph,
    get_anchor_from_baserec,
    set_anchor_in_baserec,
)

# dotted glyph -> its dotless form
DOTLESS = {
    "uni1ECB": "uni1ECB.dotless",   # ị
    "uni1E2D": "uni1E2D.dotless",   # ḭ
    "iogonek": "iogonek.dotless",   # į
    "uni029D": "uni029D.dotless",   # ʝ
    # Cyrillic і ј (Ukrainian, Belarusian stress marks: і́), 2026-11-27: their own dotless forms,
    # since in the semibold styles they are drawn apart from Latin i j (semibold і 316 wide, i 286)
    "uni0456": "uni0456.dotless",   # і
    "uni0458": "uni0458.dotless",   # ј
}

# A contour whose bottom is above this is the dot (x-heights 436-447, dot bottoms 510-547)
DOT_MIN_Y = 480


def _contours(recording):
    out, cur = [], []
    for op, args in recording:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            out.append(cur)
            cur = []
    return out


def _bounds(recording):
    pen = BoundsPen(None)
    for op, args in recording:
        getattr(pen, op)(*args)
    return pen.bounds


def add_dotless_glyphs(ttfont, font_key):
    """Add the dotless form of each DOTLESS glyph the font has. Returns report lines."""
    glyphset = ttfont.getGlyphSet()
    report = []
    for dotted, dotless in DOTLESS.items():
        if dotted not in glyphset:
            report.append(f"dotless: {dotted} not in the font; SKIPPED")
            continue
        if dotless in glyphset:
            continue
        pen = RecordingPen()
        glyphset[dotted].draw(pen)
        contours = _contours(pen.value)
        dots = [c for c in contours if _bounds(c)[1] > DOT_MIN_Y]
        if len(dots) != 1:
            raise ValueError(f"{font_key} {dotted}: expected one dot contour above {DOT_MIN_Y}, found {len(dots)}")
        outline = [seg for c in contours if c is not dots[0] for seg in c]
        advance = glyphset[dotted].width
        _set_outline(ttfont, dotless, outline)          # creates the glyph (GDEF mark, zero advance)
        _replace_outline(ttfont, dotless, outline, advance)
        ttfont["GDEF"].table.GlyphClassDef.classDefs[dotless] = 1   # base
        dot = tuple(round(v) for v in _bounds(dots[0]))
        report.append(f"dotless: added {dotless} ({dotted} without its dot {dot}), advance {advance}")
    return report


def copy_dotless_anchors(ttfont, lookup_index):
    """Give each dotless form the dotted glyph's anchors of every class but above (0). Returns report lines."""
    sub = find_mark_to_base_subtables(ttfont, lookup_index)[0]
    glyph_order = set(ttfont.getGlyphOrder())
    report = []
    for dotted, dotless in DOTLESS.items():
        if dotless not in glyph_order:
            continue
        src, _ = get_base_record_for_glyph(sub, dotted)
        if src is None:
            continue
        copied = []
        for cls in range(1, len(src.BaseAnchor)):
            xy = get_anchor_from_baserec(src, cls)
            if xy is None:
                continue
            rec, _ = ensure_base_record_for_glyph(sub, dotless)
            set_anchor_in_baserec(rec, cls, *xy)
            copied.append(f"{cls} {xy}")
        report.append(f"dotless: {dotless}: anchors copied from {dotted}: " + (", ".join(copied) or "none"))
    return report
