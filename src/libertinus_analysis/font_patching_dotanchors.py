# font_patching_dotanchors.py
"""
Dot lookup of the Libertinus patching pipeline (stage 9b).

The main mark-to-base lookup puts every above mark at the base's above
anchor, which on an ascender letter is at the ascender reference, and every
below mark at the descender reference on a descender letter. The designer
placed a dot differently in the precomposed letters: ḃ ḋ ḣ have the dot at
the height of ȧ ṅ, beside the ascender, and ỵ at the height of ạ ṇ, beside
the tail, in all four styles. This stage restores that convention for the
dots only, without changing the anchor model of the main lookup.

It appends a second mark-to-base lookup to the `mark` feature, after the
main one, with two classes: 0 the dot above (U+0307), 1 the dot below
(U+0323), and optionally the vertical lines U+030D / U+0329 in the same
classes (data/dot_letters.py). Its mark anchors are copied from the main
lookup. Its bases are the letters listed in data/dot_letters.py, their
derived letters, and the precomposed letters that inherit from them. HarfBuzz
applies the lookups in LookupList order and a later attachment replaces the
earlier one, so for a listed base the dot lookup's anchor wins; a base it does
not list, or lists without an anchor for that class, keeps the main lookup's.

Dot anchors (see data/dot_letters.py for the model): Y is the x-height
reference (above) or baseline reference (below) of ANCHOR_Y_REF_OPT; X is
taken from the designer's precomposed letter where it has the dot at the
x-height-letter height, inherited (derived letters, fit_base), or else the
model's X for the letter's x-height body pushed sideways to MIN_GAP.
"""

import math
import unicodedata

import pathops
from fontTools.ttLib.tables import otTables

from .fontmetrics_helpers import ANCHOR_Y_REF_OPT, SHIFT_K, SLOPE, VERTICAL_THRESHOLDS_OPT
from .font_patching_inherit import (
    MIN_FIT,
    PointPen,
    SegmentPen,
    find_mark_to_base_subtables,
    fit_base,
    glyph_points,
    glyph_segments,
)
from .font_patching_precomposed_anchors import (
    DOTLESS_SOURCE,
    get_base_cp_from_unicode,
    load_precomposed_letters,
)

# side: 0 above, 2 below (the main lookup's class numbers); the dot lookup's own class per side
DOT_CLASS = {0: 0, 2: 1}
DOT_MARK = {0: 0x0307, 2: 0x0323}
LINE_MARK = {0: 0x030D, 2: 0x0329}
REF = {0: "xh", 2: "base"}

STEP = 4          # units between X positions tried when pushing the dot clear
MAX_PUSH = 200    # farthest the dot is pushed from the model's X
WINDOW = 150      # gaps beyond this are not measured (reported as >WINDOW)
DOT_HEIGHT_TOL = 15   # a precomposed dot within this of ȧ's (ạ's) dot height follows the convention
GAP_LETTERS = (0x1E03, 0x1E0B, 0x1E23)   # ḃ ḋ ḣ: the designer's closest dots set MIN_GAP


def load_dot_letters():
    mod = __import__("data.dot_letters", fromlist=["DOT_ABOVE"])
    return mod


def load_derived():
    mod = __import__("data.derived_letters", fromlist=["derived"])
    return mod.derived


def _style(font_key):
    return font_key.removesuffix("_patch")


# ------------------------------------------------------------
# Geometry
# ------------------------------------------------------------

def _path(glyphset, glyph_name, dx=0, dy=0):
    from fontTools.pens.transformPen import TransformPen
    p = pathops.Path()
    glyphset[glyph_name].draw(TransformPen(pathops.PathPen(p, glyphSet=glyphset), (1, 0, 0, 1, dx, dy)))
    return p


def _seg_dist(px, py, seg):
    (x0, y0), (x1, y1) = seg
    vx, vy = x1 - x0, y1 - y0
    L = vx * vx + vy * vy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / L))
    dx, dy = x0 + t * vx - px, y0 + t * vy - py
    return math.sqrt(dx * dx + dy * dy)


def _gap(pts, segs, mark_path=None, base_path=None):
    """Smallest distance from the points to the segments (0 if the paths overlap); WINDOW if beyond it."""
    if mark_path is not None and base_path is not None:
        if abs(pathops.op(mark_path, base_path, pathops.PathOp.INTERSECTION).area) > 1:
            return 0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    lo_x, hi_x, lo_y, hi_y = min(xs) - WINDOW, max(xs) + WINDOW, min(ys) - WINDOW, max(ys) + WINDOW
    near = [s for s in segs
            if not (max(s[0][0], s[1][0]) < lo_x or min(s[0][0], s[1][0]) > hi_x
                    or max(s[0][1], s[1][1]) < lo_y or min(s[0][1], s[1][1]) > hi_y)]
    best = WINDOW
    for px, py in pts[::2]:
        for s in near:
            d = _seg_dist(px, py, s)
            if d < best:
                best = d
    return round(best)


class _Base:
    """A base glyph's outline, for gap measurements."""

    def __init__(self, ttfont, glyph_name):
        gs = ttfont.getGlyphSet()
        self.segs = glyph_segments(gs, glyph_name)
        self.path = _path(gs, glyph_name)


def mark_gap(ttfont, base, mark_glyph, mark_xy, base_xy):
    """Gap between a mark attached at base_xy (mark anchor mark_xy) and the base (_Base)."""
    gs = ttfont.getGlyphSet()
    dx, dy = base_xy[0] - mark_xy[0], base_xy[1] - mark_xy[1]
    pts = [(x + dx, y + dy) for x, y in glyph_points(gs, mark_glyph)]
    return _gap(pts, base.segs, _path(gs, mark_glyph, dx, dy), base.path)


def _contours(ttfont, glyph_name):
    p = _path(ttfont.getGlyphSet(), glyph_name)
    p.simplify()
    out = []
    for c in p.contours:
        q = pathops.Path()
        c.draw(q.getPen())
        out.append(q)
    return out


def _dot_contour(ttfont, glyph_name, side):
    """The dot of a precomposed letter: its small contour above the x-height (side 0) or below the baseline (2)."""
    best = None
    for c in _contours(ttfont, glyph_name):
        x0, y0, x1, y1 = c.bounds
        if x1 - x0 > 150 or y1 - y0 > 150:
            continue
        if (side == 0 and y0 > 300) or (side == 2 and y1 < 0):
            if best is None or (y0 if side == 0 else -y1) < (best.bounds[1] if side == 0 else -best.bounds[3]):
                best = c
    return best


def designer_gap(ttfont, glyph_name, side):
    """Gap between the dot of a precomposed letter and the rest of it."""
    cs = _contours(ttfont, glyph_name)
    dot = _dot_contour(ttfont, glyph_name, side)
    if dot is None:
        return None
    pen = PointPen(None)
    dot.draw(pen)
    segs = []
    for c in cs:
        if c is dot or c.bounds == dot.bounds:
            continue
        sp = SegmentPen(None)
        c.draw(sp)
        segs.extend(sp.segs)
    return _gap(pen.pts, segs)


def min_gap(ttfont):
    """MIN_GAP of the style: the designer's closest dot among ḃ ḋ ḣ."""
    cmap = ttfont.getBestCmap()
    gaps = [designer_gap(ttfont, cmap[cp], 0) for cp in GAP_LETTERS if cp in cmap]
    return min(g for g in gaps if g is not None)


# ------------------------------------------------------------
# Main lookup's mark anchors
# ------------------------------------------------------------

def main_mark_anchor(ttfont, lookup_index, mark_glyph):
    sub = find_mark_to_base_subtables(ttfont, lookup_index)[0]
    mc = sub.MarkCoverage.glyphs
    if mark_glyph not in mc:
        return None
    a = sub.MarkArray.MarkRecord[mc.index(mark_glyph)].MarkAnchor
    return a.XCoordinate, a.YCoordinate


# ------------------------------------------------------------
# Dot anchor candidates
# ------------------------------------------------------------

def _body(ttfont, glyph_name, style):
    """The ink between the baseline and the x-height (the letter's x-height body), as a path."""
    th = VERTICAL_THRESHOLDS_OPT[style]
    lo, hi = th["base"]["lo"], th["xh"]["hi"]
    band = pathops.Path()
    pen = band.getPen()
    pen.moveTo((-2000, lo)); pen.lineTo((3000, lo)); pen.lineTo((3000, hi)); pen.lineTo((-2000, hi)); pen.closePath()
    return pathops.op(_path(ttfont.getGlyphSet(), glyph_name), band, pathops.PathOp.INTERSECTION)


def _body_bounds(ttfont, glyph_name, style):
    b = _body(ttfont, glyph_name, style).bounds
    return b if b != (0, 0, 0, 0) else None


def body_extent(ttfont, glyph_name, style):
    """The x-height body's extent across the slant: (min, max) of x - y tan over its ink, or None."""
    pen = PointPen(None)
    _body(ttfont, glyph_name, style).draw(pen)
    if not pen.pts:
        return None
    slope = SLOPE[style]
    xs = [x - y * slope for x, y in pen.pts]
    return min(xs), max(xs)


def dot_centre_offset(ttfont, mark_glyph, mark_xy):
    """The dot's outline centre relative to its mark anchor."""
    from fontTools.pens.boundsPen import BoundsPen
    gs = ttfont.getGlyphSet()
    bp = BoundsPen(gs)
    gs[mark_glyph].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    return (x0 + x1) / 2 - mark_xy[0], (y0 + y1) / 2 - mark_xy[1]


def over_body(x, y, offset, extent, slope):
    """Whether a dot attached at (x, y) has its centre within the body's extent across the slant."""
    cx, cy = x + offset[0], y + offset[1]
    c = cx - cy * slope
    return extent[0] <= c <= extent[1]


def model_x(ttfont, glyph_name, style, side):
    """The model's X for the x-height body: roman, its ink midpoint; italic, the advance lane at Y, less K."""
    y = ANCHOR_Y_REF_OPT[style][REF[side]]
    slope = SLOPE[style]
    if slope == 0.0:
        b = _body_bounds(ttfont, glyph_name, style)
        if b is None:
            return None
        return (b[0] + b[2]) / 2.0
    k = SHIFT_K.get(style, {}).get(str(side), 0)
    return ttfont["hmtx"][glyph_name][0] / 2.0 + y * slope - k


def push_clear(ttfont, base, mark_glyph, mark_xy, x0, y, need, inside=None):
    """
    The X nearest x0 where the mark keeps a gap of at least need, and that
    gap; (None, best gap) if none. inside(x) limits the positions tried (the
    dot over the x-height body).
    """
    best = (None, -1)
    for d in sorted(range(-MAX_PUSH, MAX_PUSH + 1, STEP), key=lambda d: (abs(d), -d)):
        x = round(x0 + d)
        if inside is not None and not inside(x):
            continue
        g = mark_gap(ttfont, base, mark_glyph, mark_xy, (x, y))
        if g >= need:
            return x, g
        if g > best[1]:
            best = (None, g)
    return best


def precomposed_dot_x(ttfont, font_key, cp, side, mark_xy, ref_dot_y0):
    """
    X of the dot anchor that makes cp + dot match the designer's precomposed
    letter, if it exists and has the dot at the x-height-letter height
    (ref_dot_y0, the bottom (side 0) or top (side 2) of ȧ's / ạ's dot).
    Returns (x, implied_y, note) or (None, None, note).
    """
    cmap = ttfont.getBestCmap()
    pc = unicodedata.normalize("NFC", chr(cp) + chr(DOT_MARK[side]))
    if len(pc) != 1 or ord(pc) not in cmap:
        return None, None, "no precomposed letter"
    pc_glyph, base_glyph = cmap[ord(pc)], cmap[cp]
    dot = _dot_contour(ttfont, pc_glyph, side)
    if dot is None:
        return None, None, f"{pc}: no dot found"
    x0, y0, x1, y1 = dot.bounds
    edge = y0 if side == 0 else y1
    if abs(edge - ref_dot_y0) > DOT_HEIGHT_TOL:
        return None, None, f"{pc}: the designer's dot is not at the x-height-letter height ({round(edge)} vs {round(ref_dot_y0)})"
    gs = ttfont.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(gs)
    gs[cmap[DOT_MARK[side]]].draw(bp)
    mx0, my0, mx1, my1 = bp.bounds
    # where the base sits inside the precomposed glyph (semibold italic often builds it 12 right)
    guess = ((x0 + x1) / 2, ANCHOR_Y_REF_OPT[_style(font_key)][REF[side]])
    dx, match, _ = fit_base(ttfont, _style(font_key), pc_glyph, base_glyph, side, guess)
    if match < MIN_FIT:
        dx = 0
    x = (x0 + x1) / 2 - dx - (mx0 + mx1) / 2 + mark_xy[0]
    implied_y = (y0 - my0 if side == 0 else y1 - my1) + mark_xy[1]
    return round(x), round(implied_y), f"from {pc}" + (f" (base shifted {dx:+d})" if dx else "")


def _ref_dot_edge(ttfont, side):
    """Bottom of the dot of ȧ (side 0) or top of the dot of ạ (side 2)."""
    cmap = ttfont.getBestCmap()
    cp = 0x0227 if side == 0 else 0x1EA1
    dot = _dot_contour(ttfont, cmap[cp], side)
    return dot.bounds[1] if side == 0 else dot.bounds[3]


def _excluded(table, cp, style):
    if cp in table:
        styles, reason = table[cp]
        if styles is None or style in styles:
            return reason
    return None


def dot_anchors(ttfont, font_key, lookup_index, letters=None):
    """
    Compute the dot anchors of the style.

    letters: {side: [codepoints]} to compute instead of data/dot_letters.py's
    lists (the test sheet passes every candidate); exclusions still apply
    unless letters is given.

    Returns (anchors, info, report): anchors {(glyph, side): (x, y)};
    info {(glyph, side): dict(cp, source, gap, x0, note)}; report lines.
    """
    style = _style(font_key)
    data = load_dot_letters()
    derived = load_derived()
    cmap = ttfont.getBestCmap()
    need = min_gap(ttfont)
    report = [f"dot lookup: MIN_GAP {need} (the closest dot of ḃ ḋ ḣ)"]
    anchors, info = {}, {}
    lists = letters or {0: data.DOT_ABOVE, 2: data.DOT_BELOW}
    excl = {0: data.EXCLUDED_ABOVE, 2: data.EXCLUDED_BELOW}

    for side in (0, 2):
        mark_glyph = cmap[DOT_MARK[side]]
        mark_xy = main_mark_anchor(ttfont, lookup_index, mark_glyph)
        y = ANCHOR_Y_REF_OPT[style][REF[side]]
        ref_edge = _ref_dot_edge(ttfont, side)
        cps = list(lists[side])
        # derived letters after their base letters
        cps.sort(key=lambda c: c in derived and derived[c][0] in cps)
        for cp in cps:
            glyph = cmap.get(cp)
            if glyph is None:
                report.append(f"U+{cp:04X}: missing from font")
                continue
            reason = None if letters else _excluded(excl[side], cp, style)
            if reason:
                report.append(f"{glyph}: side {side} excluded ({reason}); SKIPPED")
                continue
            base = _Base(ttfont, glyph)
            x = source = None
            note = ""
            x0 = model_x(ttfont, glyph, style, side)
            # 1. the designer's precomposed letter
            px, implied_y, note = precomposed_dot_x(ttfont, font_key, cp, side, mark_xy, ref_edge)
            if px is not None:
                x, source = px, "precomposed"
                if abs(implied_y - y) > 3:
                    note += f", its dot implies Y {implied_y}"
            # 2. derived letter of a listed base letter
            elif cp in derived and (cmap.get(derived[cp][0]), side) in anchors:
                b_glyph = cmap[derived[cp][0]]
                bxy = anchors[(b_glyph, side)]
                dx, match, _ = fit_base(ttfont, _style(font_key), glyph, b_glyph, side, bxy)
                if match >= MIN_FIT:
                    x, source = bxy[0] + dx, "derived"
                    note = f"from {chr(derived[cp][0])}, shift {dx:+d} (fit {match:.0%})"
                else:
                    note = f"{chr(derived[cp][0])} fits {match:.0%}; model instead"
            # 3. the model, pushed clear
            if x is None:
                if x0 is None:
                    report.append(f"{glyph}: no x-height body; SKIPPED")
                    continue
                extent = body_extent(ttfont, glyph, style)
                offset = dot_centre_offset(ttfont, mark_glyph, mark_xy)
                inside = lambda x: over_body(x, y, offset, extent, SLOPE[style])
                x, g = push_clear(ttfont, base, mark_glyph, mark_xy, x0, y, need, inside)
                if x is None:
                    info[(glyph, side)] = dict(cp=cp, source="none", gap=g, x0=round(x0),
                                               note=f"no clear position over the x-height body (best gap {max(g, 0)})")
                    report.append(f"{glyph}: side {side}: no clear position over the x-height body (best gap {max(g, 0)}); SKIPPED")
                    continue
                source = "model"
                note = f"pushed {x - round(x0):+d}" if x != round(x0) else ""
            gap = mark_gap(ttfont, base, mark_glyph, mark_xy, (x, y))
            anchors[(glyph, side)] = (x, y)
            info[(glyph, side)] = dict(cp=cp, source=source, gap=gap, x0=None if x0 is None else round(x0), note=note)
            flag = "" if gap >= need else f"  ** gap under MIN_GAP {need}"
            report.append(f"{glyph}: dot {'above' if side == 0 else 'below'} ({x}, {y}), {source}{', ' + note if note else ''}; gap {gap}{flag}")

    # precomposed letters inherit from their listed base letter
    if letters is None:
        for side, (cps, pexcl) in load_precomposed_letters().items():
            mark_glyph = cmap[DOT_MARK[side]]
            mark_xy = main_mark_anchor(ttfont, lookup_index, mark_glyph)
            for cp in cps:
                glyph = cmap.get(cp)
                if glyph is None or _excluded(pexcl, cp, style):
                    continue
                base_cp = get_base_cp_from_unicode(cp)
                if side == 2 and base_cp in DOTLESS_SOURCE:
                    base_cp = DOTLESS_SOURCE[base_cp]
                b_glyph = cmap.get(base_cp)
                if (b_glyph, side) not in anchors or (glyph, side) in anchors:
                    continue
                bxy = anchors[(b_glyph, side)]
                dx, match, _ = fit_base(ttfont, _style(font_key), glyph, b_glyph, side, bxy)
                if match < MIN_FIT:
                    report.append(f"{glyph}: base '{b_glyph}' fits {match:.0%}; no dot anchor")
                    continue
                x = bxy[0] + dx
                gap = mark_gap(ttfont, _Base(ttfont, glyph), mark_glyph, mark_xy, (x, bxy[1]))
                anchors[(glyph, side)] = (x, bxy[1])
                info[(glyph, side)] = dict(cp=cp, source="inherited", gap=gap, x0=None, note=f"from {chr(base_cp)}, shift {dx:+d}")
                flag = "" if gap >= need else f"  ** gap under MIN_GAP {need}"
                report.append(f"{glyph}: dot {'above' if side == 0 else 'below'} ({x}, {bxy[1]}) inherited from '{b_glyph}', shift {dx:+d}; gap {gap}{flag}")
    return anchors, info, report


# ------------------------------------------------------------
# The lookup
# ------------------------------------------------------------

def _anchor(x, y):
    a = otTables.Anchor()
    a.Format = 1
    a.XCoordinate, a.YCoordinate = round(x), round(y)
    return a


def dot_lookup_index(ttfont, main_index):
    """Index of the dot lookup (a mark-to-base lookup other than the main one with the dot above), or None."""
    cmap = ttfont.getBestCmap()
    dot = cmap.get(DOT_MARK[0])
    for i, lk in enumerate(ttfont["GPOS"].table.LookupList.Lookup):
        if i != main_index and lk.LookupType == 4 and dot in lk.SubTable[0].MarkCoverage.glyphs:
            return i
    return None


def build_dot_lookup(ttfont, main_index, anchors, lines=(False, False)):
    """
    Append the dot lookup (or replace an existing one) and add it to every
    `mark` feature that has the main lookup. lines: (above, below), put
    U+030D / U+0329 in the classes with the dot. Returns its index.
    """
    gpos = ttfont["GPOS"].table
    cmap = ttfont.getBestCmap()
    main = gpos.LookupList.Lookup[main_index]
    marks = []
    for side in (0, 2):
        cps = [DOT_MARK[side]] + ([LINE_MARK[side]] if lines[0 if side == 0 else 1] else [])
        for cp in cps:
            g = cmap.get(cp)
            xy = main_mark_anchor(ttfont, main_index, g) if g else None
            if xy is not None:
                marks.append((g, DOT_CLASS[side], xy))
    marks.sort(key=lambda m: ttfont.getGlyphID(m[0]))
    bases = sorted({g for g, _ in anchors}, key=ttfont.getGlyphID)

    sub = otTables.MarkBasePos()
    sub.Format = 1
    sub.LookupType = 4
    sub.ClassCount = 2
    sub.MarkCoverage = otTables.Coverage()
    sub.MarkCoverage.glyphs = [m[0] for m in marks]
    sub.MarkArray = otTables.MarkArray()
    sub.MarkArray.MarkRecord = []
    for g, cls, (x, y) in marks:
        r = otTables.MarkRecord()
        r.Class = cls
        r.MarkAnchor = _anchor(x, y)
        sub.MarkArray.MarkRecord.append(r)
    sub.MarkArray.MarkCount = len(marks)
    sub.BaseCoverage = otTables.Coverage()
    sub.BaseCoverage.glyphs = bases
    sub.BaseArray = otTables.BaseArray()
    sub.BaseArray.BaseRecord = []
    for g in bases:
        r = otTables.BaseRecord()
        r.BaseAnchor = [None, None]
        for side in (0, 2):
            if (g, side) in anchors:
                r.BaseAnchor[DOT_CLASS[side]] = _anchor(*anchors[(g, side)])
        sub.BaseArray.BaseRecord.append(r)
    sub.BaseArray.BaseCount = len(bases)

    lookup = otTables.Lookup()
    lookup.LookupType = 4
    lookup.LookupFlag = main.LookupFlag
    if hasattr(main, "MarkFilteringSet"):
        lookup.MarkFilteringSet = main.MarkFilteringSet
    lookup.SubTable = [sub]
    lookup.SubTableCount = 1

    existing = dot_lookup_index(ttfont, main_index)
    if existing is not None:
        gpos.LookupList.Lookup[existing] = lookup
        return existing
    gpos.LookupList.Lookup.append(lookup)
    index = len(gpos.LookupList.Lookup) - 1
    gpos.LookupList.LookupCount = index + 1
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag == "mark" and main_index in fr.Feature.LookupListIndex:
            fr.Feature.LookupListIndex.append(index)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
    return index


def patch_dot_lookup(ttfont, font_key, lookup_index):
    """Stage 9b: build the dot lookup. Returns (report lines, {glyph: {side: source}})."""
    data = load_dot_letters()
    anchors, info, report = dot_anchors(ttfont, font_key, lookup_index)
    index = build_dot_lookup(ttfont, lookup_index, anchors, (data.LINE_ABOVE, data.LINE_BELOW))
    report.append(f"dot lookup {index}: {len({g for g, _ in anchors})} bases")
    owners = {}
    for (g, side), d in info.items():
        if (g, side) in anchors:
            owners.setdefault(g, {})[str(side)] = d["source"]
    return report, owners
