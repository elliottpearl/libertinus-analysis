"""
Heavier rings in the semibold styles (drafted 2026-11-18, in the patch since
2026-11-21 as stage 2, font_patching_rings.py, at RING_FACTOR there).

The designer's semibold rings are no heavier than the light styles' (stroke at
the sides / at the top and bottom, de-slanted: regular 40/32, semibold 36/32
and U+0325 32/27; italic 37/27, semibold italic 37/32 and U+0325 36/31), where
other fonts' bold rings are 13-60% heavier than their regular (Noto Serif,
Pagella, Junicode, Gentium Plus) and the designer's own semibold dots 24% and
diaeresis 15%. Each ring in the semibold styles (U+030A, U+0325, U+02DA and
the precomposed letters with a ring, small caps included) is redrawn, not
scaled: two Bezier ellipses (four on-curve points at the extremes, handles
KAPPA times the radius), the outer one at the designer's own centre and outer
size, the inner one inset by the target stroke, sheared about the centre at the
declared slant in semibold italic, every point rounded to a whole unit. Target
stroke = FACTOR x the light style's ring stroke (regular for semibold, italic
for semibold italic), never lighter than the designer's.

redraw_rings is the redraw itself (used by the patch). For the test sheet,
run_ring_draft_sheet.py writes fonts/LibertinusSerif-{Semibold,SemiboldItalic}-
ringdesigner.otf (the patched font with the designer's rings put back) and
-ring{NNN}.otf (that font with the rings redrawn) for each of FACTORS.
"""
import math

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from .font_context import FONTS
from .font_patching_redraw import _replace_outline

KAPPA = 0.5523                      # Bezier circle: handle = KAPPA x radius
FACTORS = (1.15, 1.20, 1.25)    # the draft sheet's; the patch's are RING_FACTOR in font_patching_rings.py
SLANT = {"semibold": 0.0, "semibold_italic": math.tan(math.radians(11.5))}
LIGHT = {"semibold": "regular", "semibold_italic": "italic"}
RING_MARK = 0x030A
# Every glyph with a ring: U+030A, U+0325, U+02DA, the precomposed letters, small caps.
RING_CODEPOINTS = (0x030A, 0x0325, 0x02DA, 0x00C5, 0x00E5, 0x016E, 0x016F, 0x01FA, 0x01FB,
                   0x1E00, 0x1E01, 0x1E98, 0x1E99)
RING_NAMES = ("aring.sc", "uring.sc")


def _contours(glyphset, name):
    """[(recording, bounds)] per closed contour, components decomposed."""
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    out, cur = [], []
    for op, args in pen.value:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            out.append(cur)
            cur = []
    return [(c, _bounds(c)) for c in out]


def _bounds(rec, t=0.0):
    """Bounds of a recording, de-slanted (x - t y) when t is given."""
    bp = BoundsPen(None)
    tp = TransformPen(bp, (1, 0, -t, 1, 0, 0))
    for op, args in rec:
        getattr(tp, op)(*args)
    return bp.bounds


def find_rings(glyphset, name, size, t):
    """Indices (outer, inner) of the ring contour pairs in a glyph: an outer contour
    within 25% of `size` (de-slanted width, height) with a contour nested inside it."""
    cs = _contours(glyphset, name)
    rings = []
    for i, (oc, _) in enumerate(cs):
        ob = _bounds(oc, t)
        w, h = ob[2] - ob[0], ob[3] - ob[1]
        if not (0.75 * size[0] < w < 1.25 * size[0] and 0.75 * size[1] < h < 1.25 * size[1]):
            continue
        for j, (ic, _) in enumerate(cs):
            ib = _bounds(ic, t)
            if j != i and ob[0] < ib[0] and ib[2] < ob[2] and ob[1] < ib[1] and ib[3] < ob[3]:
                rings.append((i, j))
    return cs, rings


def _w(rec, t):
    b = _bounds(rec, t)
    return b[2] - b[0]


def _h(rec, t):
    b = _bounds(rec, t)
    return b[3] - b[1]


def ring_metrics(outer, inner, t):
    """De-slanted centre, radii and stroke (sides, top/bottom) of a ring."""
    ob, ib = _bounds(outer, t), _bounds(inner, t)
    cx, cy = (ob[0] + ob[2]) / 2, (ob[1] + ob[3]) / 2
    rx, ry = (ob[2] - ob[0]) / 2, (ob[3] - ob[1]) / 2
    sx = (ib[0] - ob[0] + ob[2] - ib[2]) / 2
    sy = (ib[1] - ob[1] + ob[3] - ib[3]) / 2
    return cx, cy, rx, ry, sx, sy


def _ellipse(cx, cy, rx, ry, t, clockwise):
    """Closed 4-point Bezier ellipse with de-slanted centre (cx, cy), re-slanted by x += t y
    (the inverse of _bounds' de-slant); points rounded. Counter-clockwise starts left,
    clockwise starts top, as the designer's rings."""
    kx, ky = KAPPA * rx, KAPPA * ry
    L, B, R, T = (cx - rx, cy), (cx, cy - ry), (cx + rx, cy), (cx, cy + ry)
    segs = [  # counter-clockwise: left -> bottom -> right -> top -> left
        (L, (cx - rx, cy - ky), (cx - kx, cy - ry), B),
        (B, (cx + kx, cy - ry), (cx + rx, cy - ky), R),
        (R, (cx + rx, cy + ky), (cx + kx, cy + ry), T),
        (T, (cx - kx, cy + ry), (cx - rx, cy + ky), L),
    ]
    if clockwise:   # top -> right -> bottom -> left -> top
        segs = [(s[3], s[2], s[1], s[0]) for s in reversed(segs)]
        segs = segs[1:] + segs[:1]

    def p(pt):
        x, y = pt
        return (round(x + t * y), round(y))
    rec = [("moveTo", (p(segs[0][0]),))]
    for _, c1, c2, end in segs:
        rec.append(("curveTo", (p(c1), p(c2), p(end))))
    rec.append(("closePath", ()))
    return rec


def ring(cx, cy, rx, ry, sx, sy, t):
    """Ring as outer (counter-clockwise) + inner (clockwise) contours; (cx, cy) de-slanted.
    Centre and radii are rounded to whole units before the shear."""
    cx, cy, rx, ry, sx, sy = (round(v) for v in (cx, cy, rx, ry, sx, sy))
    return _ellipse(cx, cy, rx, ry, t, False) + _ellipse(cx, cy, rx - sx, ry - sy, t, True)


def light_stroke(style):
    """(sides, top/bottom) of the light style's U+030A, de-slanted at its own slant.
    Read from the original light font (the patch does not change its rings)."""
    tt = TTFont(str(FONTS[LIGHT[style]]["path"]))
    gs = tt.getGlyphSet()
    t = SLANT[style]
    cs, rings = find_rings(gs, tt.getBestCmap()[RING_MARK], (176, 170), t)
    (i, j), = rings
    return ring_metrics(cs[i][0], cs[j][0], t)[4:]


def ring_glyphs(tt):
    """Names of the glyphs with a ring in a font."""
    cmap = tt.getBestCmap()
    gs = tt.getGlyphSet()
    return [cmap[c] for c in RING_CODEPOINTS if c in cmap] + [n for n in RING_NAMES if n in gs]


def redraw_rings(tt, style, factor):
    """Redraw every ring of `tt` (a font of `style`) in place at `factor` x the light
    style's stroke, never lighter than the ring it replaces.
    Returns [(glyph, old (sx, sy) or "counter" or None, new (sx, sy) or None)];
    None, None: no ring found in the glyph (left as it is)."""
    t = SLANT[style]
    lsx, lsy = light_stroke(style)
    gs = tt.getGlyphSet()
    mark = tt.getBestCmap()[RING_MARK]
    cs, ((i, j),) = find_rings(gs, mark, (176, 170), t)
    _, _, mrx, mry, msx, msy = ring_metrics(cs[i][0], cs[j][0], t)
    tsx, tsy = max(msx, factor * lsx), max(msy, factor * lsy)
    report, new = [], {}
    for name in ring_glyphs(tt):
        contours, rings = find_rings(gs, name, (2 * mrx, 2 * mry), t)
        if not rings:
            # Å Ǻ: the ring is merged with the apex (and Ǻ's acute), so only its counter is
            # a contour of its own: inset the counter by what the mark's stroke gains.
            counters = [k for k, (c, _) in enumerate(contours)
                        if abs(_w(c, t) - 2 * (mrx - msx)) < 0.2 * 2 * (mrx - msx)
                        and abs(_h(c, t) - 2 * (mry - msy)) < 0.2 * 2 * (mry - msy)]
            if len(counters) != 1:
                report.append((name, None, None))
                continue
            k, = counters
            b = _bounds(contours[k][0], t)
            rec = [seg for n, (c, _) in enumerate(contours) if n != k for seg in c]
            cx, cy = round((b[0] + b[2]) / 2), round((b[1] + b[3]) / 2)
            rx, ry = round((b[2] - b[0]) / 2 - (tsx - msx)), round((b[3] - b[1]) / 2 - (tsy - msy))
            rec += _ellipse(cx, cy, rx, ry, t, True)
            new[name] = rec
            report.append((name, "counter", (round(tsx - msx), round(tsy - msy))))
            continue
        drop = {k for pr in rings for k in pr}
        rec = [seg for k, (c, _) in enumerate(contours) if k not in drop for seg in c]
        for i, j in rings:
            cx, cy, rx, ry, sx, sy = ring_metrics(contours[i][0], contours[j][0], t)
            nsx, nsy = max(sx, factor * lsx), max(sy, factor * lsy)
            rec += ring(cx, cy, rx, ry, nsx, nsy, t)
            report.append((name, (round(sx), round(sy)), (round(nsx), round(nsy))))
        new[name] = rec
    for name, rec in new.items():
        _replace_outline(tt, name, rec, tt["hmtx"][name][0])
    return report


def designer_rings_font(style, out_path=None):
    """The patched font of `style` with the designer's rings put back (the original
    font's outlines of every ring glyph), for the draft sheet's comparisons."""
    tt = TTFont(str(FONTS[style + "_patch"]["path"]))
    orig = TTFont(str(FONTS[style]["path"]))
    ogs = orig.getGlyphSet()
    for name in ring_glyphs(tt):
        pen = DecomposingRecordingPen(ogs)
        ogs[name].draw(pen)
        _replace_outline(tt, name, pen.value, orig["hmtx"][name][0])
    if out_path:
        tt.save(out_path)
    return tt


def draft_rings(style, factor, out_path=None):
    """Patched font of `style` with every ring redrawn at `factor` x the light style's
    stroke, starting from the designer's rings. Returns (font, report) (see redraw_rings)."""
    tt = designer_rings_font(style)
    report = redraw_rings(tt, style, factor)
    if out_path:
        tt.save(out_path)
    return tt, report
