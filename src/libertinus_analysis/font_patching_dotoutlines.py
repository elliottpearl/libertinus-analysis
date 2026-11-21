# font_patching_dotoutlines.py
"""
Dot outlines (stage 2 of the Libertinus patching pipeline, 2026-11-21).

The designer's dots are consistent except in the combining marks below:

- In every style the precomposed letters use one single dot, above and below
  (ȧ ḃ ṅ …, ạ ḅ ọ … ỵ): the dot of the spacing dot accent U+02D9. The
  combining dot below U+0323, and the one precomposed letter that uses it
  (ṃ), have a different one: larger in regular (108 vs 100) and italic
  (110×108 vs 98×96), smaller in semibold (109 vs 124), about the same in
  semibold italic (122 vs 120).
- The precomposed diaeresis letters, above (ä ë ï ö ü ÿ) and below (ṳ), use
  the outline of U+0308. The combining diaeresis below U+0324 is instead two
  U+0323 dots 198 apart in every style (copied), against U+0308's smaller dots
  160-181 apart.

This stage gives U+0323 and ṃ's dot the dot of U+02D9, and U+0324 the outline
of U+0308. Each new outline keeps the old one's top edge (so the clearance
under the letter, which the curated mark anchors set, does not change) and its
axis across the slant (x - y tan θ of the centre, so the mark-axis rule still
holds).

It also moves the dot of ỵ right in the italic styles (YDOT_MOVE): the
designer placed it with the roman offset from ạ's dot (+151), which in italic
leaves a gap of 14 to the slanted tail, against 45-95 for every other
precomposed dot below (median 58). The dot lookup takes y's dot X from ỵ,
so composed y, ɏ, ƴ, ỿ follow.
"""

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen

from .fontmetrics_helpers import SLOPE

YDOT_MOVE = {"italic": 52, "semibold_italic": 12}   # units right; gap 14 -> ~58 (italic median), 43 -> ~53 (semibold italic, ạ 51)
DOT_MAX = 160     # a contour narrower and lower than this is a dot


def _bounds(glyphset, glyph):
    bp = BoundsPen(glyphset)
    glyphset[glyph].draw(bp)
    return bp.bounds


def _contours(glyphset, glyph):
    rec = RecordingPen()
    glyphset[glyph].draw(rec)
    cur = []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            yield cur
            cur = []


def _replay(contour):
    def draw(pen):
        for op, args in contour:
            getattr(pen, op)(*args)
    return draw


def _measure(draw, slope):
    """(top, centre across the slant): the outline's ymax, and the centre of its de-slanted ink bounds."""
    plain, sheared = BoundsPen(None), BoundsPen(None)
    draw(plain)
    draw(TransformPen(sheared, (1, 0, -slope, 1, 0, 0)))
    return plain.bounds[3], (sheared.bounds[0] + sheared.bounds[2]) / 2, plain.bounds


def _is_dot_below(contour):
    bp = BoundsPen(None)
    _replay(contour)(bp)
    x0, y0, x1, y1 = bp.bounds
    return y1 < 0 and x1 - x0 < DOT_MAX and y1 - y0 < DOT_MAX


def _offset(old_draw, new_draw, slope):
    """Whole-unit translation that puts the new outline at the old one's top edge and on its axis across the slant
    (the centre of the de-slanted ink bounds, as the mark-axis rule measures it)."""
    otop, oc, _ = _measure(old_draw, slope)
    ntop, nc, _ = _measure(new_draw, slope)
    dy = round(otop - ntop)
    dx = round(oc - nc + dy * slope)
    return dx, dy


def _write(ttfont, glyph, draw):
    """Replace glyph's charstring by what draw(pen) draws; the advance is kept."""
    gs = ttfont.getGlyphSet()
    cff = ttfont["CFF "].cff
    td = cff.topDictIndex[0]
    pen = T2CharStringPen(ttfont["hmtx"][glyph][0], gs)
    draw(pen)
    td.CharStrings[glyph] = pen.getCharString(private=td.Private, globalSubrs=cff.GlobalSubrs)


def _replace_mark(ttfont, target, source, slope):
    gs = ttfont.getGlyphSet()
    old = _bounds(gs, target)
    dx, dy = _offset(gs[target].draw, gs[source].draw, slope)
    _write(ttfont, target, lambda pen: gs[source].draw(TransformPen(pen, (1, 0, 0, 1, dx, dy))))
    nb = _bounds(ttfont.getGlyphSet(), target)
    return (f"{target}: outline of {source}, {round(old[2] - old[0])}x{round(old[3] - old[1])} -> "
            f"{round(nb[2] - nb[0])}x{round(nb[3] - nb[1])}, top {round(old[3])} kept")


def _replace_dot_contour(ttfont, glyph, source, slope):
    """Replace the dot below of a precomposed glyph by source's outline (top edge and axis kept)."""
    gs = ttfont.getGlyphSet()
    contours = list(_contours(gs, glyph))
    dots = [c for c in contours if _is_dot_below(c)]
    if len(dots) != 1:
        raise ValueError(f"{glyph}: expected one dot below, found {len(dots)}")
    old = _measure(_replay(dots[0]), 0)[2]
    dx, dy = _offset(_replay(dots[0]), gs[source].draw, slope)

    def draw(pen):
        for c in contours:
            if c is dots[0]:
                gs[source].draw(TransformPen(pen, (1, 0, 0, 1, dx, dy)))
            else:
                for op, args in c:
                    getattr(pen, op)(*args)
    _write(ttfont, glyph, draw)
    return f"{glyph}: dot below replaced by {source}'s, {round(old[2] - old[0])} wide -> {round(_bounds(gs, source)[2] - _bounds(gs, source)[0])}"


def _move_dot_contour(ttfont, glyph, move):
    gs = ttfont.getGlyphSet()
    contours = list(_contours(gs, glyph))
    dots = [c for c in contours if _is_dot_below(c)]
    if len(dots) != 1:
        raise ValueError(f"{glyph}: expected one dot below, found {len(dots)}")

    def draw(pen):
        for c in contours:
            t = (lambda p: (p[0] + move, p[1])) if c is dots[0] else (lambda p: p)
            for op, args in c:
                getattr(pen, op)(*[t(p) for p in args])
    _write(ttfont, glyph, draw)
    return f"{glyph}: dot below moved {move:+d}"


def patch_dot_outlines(ttfont, font_key):
    """Stage 2: U+0323 and ṃ's dot take U+02D9's dot, U+0324 takes U+0308's outline; italic ỵ's dot moves right."""
    style = font_key.removesuffix("_patch")
    slope = SLOPE[style]
    cmap = ttfont.getBestCmap()
    dot, diaeresis = cmap[0x02D9], cmap[0x0308]
    report = [
        _replace_mark(ttfont, cmap[0x0323], dot, slope),
        _replace_mark(ttfont, cmap[0x0324], diaeresis, slope),
        _replace_dot_contour(ttfont, cmap[0x1E43], dot, slope),
    ]
    if style in YDOT_MOVE:
        report.append(_move_dot_contour(ttfont, cmap[0x1EF5], YDOT_MOVE[style]))
    return report
