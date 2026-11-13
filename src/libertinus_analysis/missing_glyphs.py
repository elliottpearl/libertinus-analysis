# missing_glyphs.py
"""
Drafts of the base letters that the non-regular styles lack (to-do item
"Create the glyphs that are missing in the non-regular styles", 2026-11-13).

The base groups reach further than the designer's coverage: Ɇ Ɍ Ɏ ɏ ꝥ ꞓ Ɱ ꭒ
ỿ Ɋ Ỻ Ⅎ exist only in regular, Ɉ is missing in italic and semibold italic,
ẜ ẝ in semibold and semibold italic. This module drafts each of them in the
styles that lack it and writes test fonts fonts/*-draft.otf (the patched
fonts plus the drafts) for the test sheet tex/missing_glyphs_test_sheet.tex.
It is not a patch stage.

How the drafts are built (rebuilt 2026-11-13): see "Constructions" below.
Every draft is the base letter's own contours plus a part (a glyph of the
font, such as a stroke overlay mark, or one simple contour taken from the
designer's glyph), or a splice of two contours (glyph_construction.py); no
boolean operations, and the components overlap. The earlier recipes
(`stroke`, `graft`, `copied` + unions) remain only where a candidate kept for
comparison uses them.

The recipes that take parts from other letters are run in regular too, and
compared with the designer's glyph (PUA U+F600 and up in the regular draft
font), as a check of the recipe.
"""

import math
import statistics

import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from . import glyph_construction as gc
from .config import FONTS_DIR, TEX_DIR
from .font_patching_addmarks import embolden
from .font_patching_inherit import SegmentPen, intervals
from .fontmetrics_helpers import SLOPE

STYLES = {
    "regular": "LibertinusSerif-Regular",
    "italic": "LibertinusSerif-Italic",
    "semibold": "LibertinusSerif-Semibold",
    "semibold_italic": "LibertinusSerif-SemiboldItalic",
}
ORDER = ["regular", "italic", "semibold", "semibold_italic"]

MIN_PIECE = 60       # units²: smaller pieces of a difference are slivers
PUSH = 2.0           # units: a piece's points on the base's edges go this far into its ink

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

def _path(glyphset, name, matrix=(1, 0, 0, 1, 0, 0)):
    path = pathops.Path()
    glyphset[name].draw(TransformPen(path.getPen(glyphSet=glyphset), matrix))
    return path


def _moved(path, matrix):
    out = pathops.Path()
    path.draw(TransformPen(out.getPen(), matrix))
    return out


def _op(a, b, operator):
    return pathops.op(a, b, operator, fix_winding=True, keep_starting_points=False)


def _union(*paths):
    out = paths[0]
    for p in paths[1:]:
        out = _op(out, p, pathops.PathOp.UNION)
    return out


def _diff(a, b):
    return _op(a, b, pathops.PathOp.DIFFERENCE)


def _inter(a, b):
    return _op(a, b, pathops.PathOp.INTERSECTION)


def _sbox(x0, y0, x1, y1, slope=0.0):
    """A box in sheared coordinates: x0, x1 are x - y tan at each height."""
    p = pathops.Path()
    p.moveTo(x0 + y0 * slope, y0)
    p.lineTo(x1 + y0 * slope, y0)
    p.lineTo(x1 + y1 * slope, y1)
    p.lineTo(x0 + y1 * slope, y1)
    p.close()
    return p


def _recording(path):
    pen = RecordingPen()
    path.draw(pen)
    return pen.value


def _from_recording(recording):
    path = pathops.Path()
    pen = path.getPen()
    for operator, operands in recording:
        getattr(pen, operator)(*operands)
    return path


def _contours(path):
    return [c for c in path.contours]


def _segs(path):
    pen = SegmentPen(None)
    path.draw(pen)
    return pen.segs


def _edges(path, y, slope):
    """Sorted ink edges of the outline at height y, in sheared coordinates."""
    return [x for pair in intervals(_segs(path), slope, y) for x in pair]


def _interval(path, y, slope, index):
    pairs = intervals(_segs(path), slope, y)
    return pairs[index]


def _xor_ratio(a, b):
    """Ink of a XOR b over the ink of b."""
    return abs(_op(a, b, pathops.PathOp.XOR).area) / abs(b.area)


def _fit_dx(derived, base_of, search=range(-200, 201)):
    """The shift of the base that leaves the least of its ink outside the derived glyph."""
    best = None
    for dx in search:
        miss = abs(_diff(base_of(dx), derived).area)
        if best is None or miss < best[0]:
            best = (miss, dx)
    return best[1]


def _shape(path):
    """Area, length along its principal axis and thickness (area / length) of a piece."""
    pts = [pt for _, operands in _recording(path) for pt in operands]
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    syy = sum((y - my) ** 2 for _, y in pts)
    sxy = sum((x - mx) * (y - my) for x, y in pts)
    angle = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(angle), math.sin(angle)
    proj = [x * ux + y * uy for x, y in pts]
    length = max(proj) - min(proj)
    area = abs(path.area)
    return area, length, area / length if length else 0.0


# ------------------------------------------------------------
# A style
# ------------------------------------------------------------

class Style:
    def __init__(self, key, font=None):
        self.key = key
        self.font = font or TTFont(FONTS_DIR / f"{STYLES[key]}-patch.otf")
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.slope = SLOPE[key]

    def name(self, char):
        return self.cmap.get(ord(char), char) if len(char) == 1 else char

    def path(self, char, dx=0.0):
        return _path(self.glyphs, self.name(char), (1, 0, 0, 1, dx, 0))

    def advance(self, char):
        return self.font["hmtx"].metrics[self.name(char)][0]

    def has(self, char):
        return ord(char) in self.cmap


def _run(path, x, y, step=0.5, vertical=True):
    """Length of the ink run through (x, y), vertical or horizontal."""
    def inside(t):
        return path.contains((x, y + t) if vertical else (x + t, y))
    if not inside(0):
        return 0.0
    up = down = 0.0
    while inside(up + step):
        up += step
    while inside(-(down + step)):
        down += step
    return up + down


def _free(intervals_d, intervals_b, longest):
    """The intervals of the derived letter whose middle is outside the base's ink."""
    return [(a0, a1) for a0, a1 in intervals_d
            if a1 - a0 < longest and not any(b0 - 3 <= (a0 + a1) / 2 <= b1 + 3 for b0, b1 in intervals_b)]


def _bar_thickness(style, derived, base):
    """
    A horizontal bar: the median vertical ink run, over every column where
    the derived letter has ink outside its base letter's.
    """
    d = _moved(style.path(derived), (0, 1, 1, 0, 0, 0))    # x and y swapped
    b = _moved(style.path(base), (0, 1, 1, 0, 0, 0))
    runs = [a1 - a0
            for x in range(int(d.bounds[1]), int(d.bounds[3]), 4)
            for a0, a1 in _free(intervals(_segs(d), 0.0, x), intervals(_segs(b), 0.0, x), 90)]
    return statistics.median(runs)


def _diagonal_thickness(style, derived, base):
    """
    A diagonal stroke: at every height where the derived letter has exactly
    one interval outside its base letter's ink, that interval's width and
    middle; the middles give the stroke's direction, and the median width
    times the cosine of its angle from the vertical is the thickness.
    """
    d, b = style.path(derived), style.path(base)
    samples = []
    for y in range(int(d.bounds[1]), int(d.bounds[3]), 5):
        free = _free(intervals(_segs(d), 0.0, y), intervals(_segs(b), 0.0, y), 200)
        if len(free) == 1:
            samples.append((y, (free[0][0] + free[0][1]) / 2, free[0][1] - free[0][0]))
    ys = [y for y, _, _ in samples]
    xs = [x for _, x, _ in samples]
    my, mx = statistics.mean(ys), statistics.mean(xs)
    dxdy = (sum((y - my) * (x - mx) for y, x in zip(ys, xs))
            / sum((y - my) ** 2 for y in ys))
    return statistics.median(w for _, _, w in samples) * math.cos(math.atan(dxdy))


def _ref_thickness(style, ref):
    """
    Thickness of the style's own analogous stroke, measured where it lies
    outside its base letter's ink (in the italic styles Đ đ Ø ɇ … are drawn
    afresh, not built on D d O e, so the difference of the outlines is not
    the stroke alone).
    """
    derived, base = ref
    if derived in DIAGONALS:
        return _diagonal_thickness(style, derived, base)
    return _bar_thickness(style, derived, base)


# ------------------------------------------------------------
# Recipes
# ------------------------------------------------------------

def _map_point(x, y, src_base, src_slope, dst_base, dst_slope, fallback):
    """Carry a point from the source base to the target base (see `stroke`)."""
    xs = x - y * src_slope
    es = _edges(src_base, y, src_slope)
    ed = _edges(dst_base, y, dst_slope)
    own_edges = bool(es) and len(es) == len(ed)
    if not own_edges:
        es, ed = fallback
    if own_edges:
        # A point on an edge of the base goes PUSH into the base's ink, so that
        # the piece overlaps the base rather than touching it.
        for i, e in enumerate(es):
            if abs(xs - e) < 0.5:
                return ed[i] + (PUSH if i % 2 == 0 else -PUSH) + y * dst_slope
    if xs <= es[0]:
        xd = ed[0] + (xs - es[0])
    elif xs >= es[-1]:
        xd = ed[-1] + (xs - es[-1])
    else:
        for i in range(len(es) - 1):
            if es[i] <= xs <= es[i + 1]:
                span = es[i + 1] - es[i]
                u = (xs - es[i]) / span if span else 0.0
                xd = ed[i] + u * (ed[i + 1] - ed[i])
                break
    return xd + y * dst_slope


def stroke(dst, src, char, base, ref, base_dx=None, base_dst=None, dy=0):
    """
    `char` in style dst: the pieces that src's `char` adds to src's base,
    carried to dst's base and thickened as dst's `ref` stroke is.

    base: a letter, or a list of (letter, dx) for a base of several letters
    (ỻ). ref: (derived, base) of the analogous stroke, e.g. ("Đ", "D").
    dy: move the pieces up by this much before carrying them (Ɉ in the
    italics).
    Returns (path, advance, note).
    """
    derived = src.path(char)
    if isinstance(base, str):
        if base_dx is None:
            base_dx = _fit_dx(derived, lambda x: src.path(base, x))
        src_base = src.path(base, base_dx)
        dst_base = dst.path(base, base_dx)
        added_advance = src.advance(char) - src.advance(base)
        advance = dst.advance(base) + added_advance
        base_label = f"{base} at {base_dx:+d}" if base_dx else base
    else:
        src_base = _union(*(src.path(b, dx) for b, dx in base))
        dst_base = _union(*(dst.path(b, dx) for b, dx in base_dst))
        advance = dst.advance(char) if dst.has(char) else (
            src.advance(char) + sum(dst.advance(b) - src.advance(b) for b, _ in base))
        base_label = " + ".join(f"{b} at {dx:+d}" for b, dx in base_dst)

    t_src = _ref_thickness(src, ref)
    t_dst = _ref_thickness(dst, ref)
    ratio = t_dst / t_src

    pieces = [c for c in _contours(_diff(derived, src_base)) if abs(c.area) > MIN_PIECE]
    if dy:
        pieces = [_moved(c, (1, 0, 0, 1, 0, dy)) for c in pieces]
    moved = []
    for piece in pieces:
        _, _, thickness = _shape(piece)
        y_mid = (piece.bounds[1] + piece.bounds[3]) / 2
        fallback = (_edges(src_base, y_mid, src.slope), _edges(dst_base, y_mid, dst.slope))
        if not fallback[0] or len(fallback[0]) != len(fallback[1]):
            fallback = ([src_base.bounds[0], src_base.bounds[2]], [dst_base.bounds[0], dst_base.bounds[2]])
        rec = [
            (op, tuple(
                (_map_point(x, y, src_base, src.slope, dst_base, dst.slope, fallback), y)
                for x, y in operands))
            for op, operands in _recording(piece)
        ]
        grow = (ratio - 1) * thickness / 2
        moved.append(_from_recording(embolden(rec, grow)) if abs(grow) > 0.25 else _from_recording(rec))
    note = (f"{dst.key}'s {base_label} + {len(pieces)} piece(s) of {src.key}'s {char}"
            + (f" moved up {dy}" if dy else "")
            + f"; thickness × {ratio:.2f} (own {ref[0]}: {t_dst:.1f} vs {t_src:.1f})")
    return _union(dst_base, *moved), advance, note


def _segments(path):
    """The outline's segments: ("l", [p0, p1]) or ("c", [p0, p1, p2, p3])."""
    out, cur, start = [], None, None
    for op, pts in _recording(path):
        if op == "moveTo":
            cur = start = pts[0]
        elif op == "lineTo":
            out.append(("l", [cur, pts[0]]))
            cur = pts[0]
        elif op == "curveTo":
            out.append(("c", [cur, *pts]))
            cur = pts[-1]
        elif op == "closePath":
            if cur != start:
                out.append(("l", [cur, start]))
            cur = start
    return out


def _bezier(p, t):
    if len(p) == 2:
        return tuple(p[0][k] + (p[1][k] - p[0][k]) * t for k in (0, 1))
    a, b, c, d = p
    return tuple((1 - t) ** 3 * a[k] + 3 * (1 - t) ** 2 * t * b[k] + 3 * (1 - t) * t * t * c[k]
                 + t ** 3 * d[k] for k in (0, 1))


def _segment_at(path, y, x):
    """The segment of the outline that crosses height y nearest x."""
    best = None
    for kind, p in _segments(path):
        pts = [_bezier(p, i / 40) for i in range(41)]
        for a, b in zip(pts, pts[1:]):
            if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
                xx = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                if best is None or abs(xx - x) < best[0]:
                    best = (abs(xx - x), kind, p)
    return best[1], best[2]


def _straight_end(path, y, x, down):
    """
    Where the straight edge through (x, y) ends, going down (or up): the end
    of that line, or, if the outline there is already a curve, where the
    curve begins.
    """
    kind, p = _segment_at(path, y, x)
    ys = (p[0][1], p[-1][1])
    if kind == "l":
        return min(ys) if down else max(ys)
    return max(ys) if down else min(ys)


def _merge_straight(path, y_join, tolerance=2.5):
    """
    Drop the on-curve points at the join (within 1.5 of y_join) that lie
    between two lines and within `tolerance` of the line joining their
    neighbours, so that a stem runs straight through the join, as in
    regular Ɱ (M's leg lines run on into J's hook).
    """
    out = []
    contour = []

    def flush():
        pts = [(op, a) for op, a in contour if op in ("lineTo", "moveTo", "curveTo")]
        changed = True
        while changed and len(pts) > 3:
            changed = False
            n = len(pts)
            for i in range(n):
                op, a = pts[i]
                nop, na = pts[(i + 1) % n]
                # A line ending within a unit of the next point is a sliver of the cut.
                if op == "lineTo" and abs(a[0][1] - y_join) <= 1.5 and math.dist(a[0], na[-1]) < 1.0:
                    del pts[i]
                    changed = True
                    break
                if op not in ("lineTo", "moveTo") or nop != "lineTo":
                    continue
                if op == "moveTo" and pts[i - 1][0] != "lineTo":
                    continue
                if i == 0 and pts[-1][0] != "lineTo":
                    continue
                prev = pts[i - 1][1][-1]
                here, nxt = a[0], na[0]
                if abs(here[1] - y_join) > 1.5:
                    continue
                dx, dy = nxt[0] - prev[0], nxt[1] - prev[1]
                dist = abs(dy * (here[0] - prev[0]) - dx * (here[1] - prev[1])) / math.hypot(dx, dy)
                if dist < tolerance:
                    if op == "moveTo":
                        pts[(i + 1) % n] = ("moveTo", na)
                    del pts[i]
                    changed = True
                    break
        out.extend(pts)
        out.append(("closePath", ()))

    for op, a in _recording(path):
        if op == "moveTo" and contour:
            flush()
            contour = []
        if op in ("closePath", "endPath"):
            flush()
            contour = []
            continue
        contour.append((op, a))
    if contour:
        flush()
    return _from_recording(out)


_LAST_DONOR = [None]   # the donor glyph as placed by the last graft (for OVERLAYS)


def graft(style, base, donor, y_join, cut, donor_keep, base_index, donor_index, base_path=None,
          down=True, adjust=None):
    """
    `base` with the region `cut(style, base path, y_join)` replaced by
    `donor` ∩ `donor_keep(style, donor path, y_join)`.

    y_join None: the join is where the straight edges end. For each stem edge
    (left, right), the base's stem line ends at some height (where its foot
    serif's bracket begins) and the donor's at another (where its hook's
    curve begins); the join is the higher of these over both edges (the
    lower, going up), so that both stems are straight there. The donor is
    moved so that its stem's centre line lies on the base's, at the join and
    100 above (below, going up), and scaled across to the base's width at the
    join; then the points left at the join on a straight edge are dropped,
    and each edge runs straight from the base's line into the donor's.
    Returns (path, y_join, note).
    """
    b = base_path if base_path is not None else style.path(base)
    d = j_without_crossbar(style) if donor == "J" else style.path(donor)
    probe = 250.5 if down else 150.5
    if y_join is None:
        ends = []
        for path, index in ((b, base_index), (d, donor_index)):
            x0, x1 = intervals(_segs(path), 0.0, probe)[index]
            ends += [_straight_end(path, probe, x0, down), _straight_end(path, probe, x1, down)]
        y_join = math.ceil(max(ends)) if down else math.floor(min(ends))
    h2 = y_join + (100.5 if down else -100.5)
    h1 = y_join + (2.5 if down else -2.5)  # just inside the straight part, off the end points
    (b0, b1), (d0, d1) = _interval(b, h1, 0.0, base_index), _interval(d, h1, 0.0, donor_index)
    (B0, B1), (D0, D1) = _interval(b, h2, 0.0, base_index), _interval(d, h2, 0.0, donor_index)
    k = (b1 - b0) / (d1 - d0)
    # x' = k x + C(y), C linear: the centre lines coincide at y_join and h2.
    c1 = (b0 + b1) / 2 - k * (d0 + d1) / 2
    c2 = (B0 + B1) / 2 - k * (D0 + D1) / 2
    cy = (c2 - c1) / (h2 - h1)
    part = _inter(d, donor_keep(style, d, y_join))
    part = _moved(part, (k, 0, cy, 1, c1 - cy * h1, 0))
    _LAST_DONOR[0] = _moved(d, (k, 0, cy, 1, c1 - cy * h1, 0))
    seams = [y_join]
    if adjust is not None:
        part, extra = adjust(style, part, y_join)
        seams += extra
    result = _union(_diff(b, cut(style, b, y_join)), part)
    before = sum(1 for op, _ in _recording(result) if op in ("lineTo", "curveTo"))
    for seam in seams:
        result = _merge_straight(result, seam)
    dropped = before - sum(1 for op, _ in _recording(result) if op in ("lineTo", "curveTo"))
    note = (f"{style.key}'s {base} with {donor}'s part, joined at y {y_join}; stem {d1 - d0:.0f} → {b1 - b0:.0f}"
            f" (× {k:.2f}); {dropped} point(s) at the join dropped as straight")
    return result, y_join, note


def _stem_width(style, char="I", y=300):
    x0, x1 = _interval(style.path(char), y, style.slope, 0)
    return x1 - x0


def copied(dst, src, char):
    """src's glyph, slanted to dst's angle and pushed outward by half the stems' difference."""
    path = src.path(char)
    shear = dst.slope - src.slope
    path = _moved(path, (1, 0, shear, 1, 0, 0))
    grow = (_stem_width(dst) - _stem_width(src)) / 2
    if abs(grow) > 0.5:
        top = path.bounds[3]
        path = _from_recording(embolden(_recording(path), grow))
        # Pushing outward raises the top by `grow` too: scale back to the same
        # height above the baseline (x by the shear, so the slant is kept).
        k = top / (top + grow)
        path = _moved(path, (1, 0, (k - 1) * dst.slope, k, grow, 0))
    return path, src.advance(char) + 2 * max(grow, 0), (
        f"{src.key}'s {char}" + (f" slanted (tan {shear:.3f})" if shear else "")
        + (f", pushed outward by {grow:.1f} (stem I {_stem_width(dst):.0f} vs {_stem_width(src):.0f})"
           if abs(grow) > 0.5 else ""))


def turned(style, letter):
    """
    The style's letter turned 180°, as the designer turned regular's Ⅎ Ɐ Ʌ:
    its highest point comes down to the bottom of the flat serifs (H's lowest
    point, -2 in regular), so that a pointed top (A's apex) does not
    overshoot below the baseline; across, about the middle of the advance lane
    at that height, so the sidebearings swap.
    """
    w = style.advance(letter)
    top = style.path(letter).bounds[3]
    bottom = style.path("H").bounds[1]
    cy = (top + bottom) / 2
    cx = w / 2 + cy * style.slope
    path = _path(style.glyphs, style.name(letter), (-1, 0, 0, -1, 2 * cx, 2 * cy))
    return path, w, f"{style.key}'s {letter} turned about ({cx:.0f}, {cy:.1f})"


# ------------------------------------------------------------
# The letters
# ------------------------------------------------------------

def _right_of_v(style, b, y_join):  # noqa
    """Ɱ: cut everything below y_join right of the V (the last-but-one ink interval)."""
    s = style.slope
    pairs = intervals(_segs(b), s, y_join + 2.5)   # off the vertex heights
    x = pairs[-2][1] + 10
    return _sbox(x, -400, 2000, y_join, s)


def _q_tail_cut():
    def cut(style, b, y_join):
        s = style.slope
        x0, _ = _interval(b, y_join + 2.5, s, -1)
        # From 3 units inside the stem, so that the base's ink overlaps the
        # donor's stem rather than touching it (touching left a 1-unit channel).
        return _union(_sbox(x0 + 3, -400, 2000, y_join, s), _sbox(-1000, -400, 2000, -20, s))
    return cut


def _below(style, d, y):
    return _sbox(-1000, -400, 2000, y, style.slope)


def _above(style, d, y):
    return _sbox(-1000, y, 2000, 1000, style.slope)


def _left_stem_top():
    def cut(style, b, y_join):
        s = style.slope
        (a0, a1), (c0, _) = intervals(_segs(b), s, y_join - 2.5)[:2]
        return _sbox(-1000, y_join, (a1 + c0) / 2, 1000, s)
    return cut


def draft_M_hook(style):
    path, y_join, note = graft(style, "M", "J", None, _right_of_v, _below, -1, 0)
    JOINS[("Ɱ", style.key)] = y_join
    return path, style.advance("M"), note


Q_JOIN = 200   # where q's (Ɋ's) stem and ɖ's are straight and apart from the bowl
JOINS = {}     # (char, style) -> joining height of the grafts, for the sheet's figures
OVERLAYS = {}  # (char, style) -> the donor glyph as placed by its graft, drawn under the figure


def _deepen(style, part, y_join):
    """
    Run a hook tail down to the descender: the straight stem below the join is
    lengthened and the hook below it moved down unchanged, along the stem,
    until its lowest point is at g's (the style's round descender, -238; the
    descender line is -232). Ɋ and ɋ have a descender-deep tail in Gentium
    Plus and Noto Serif and in the 1965 Kâte Bible (Priest 2004, figures
    31-32); Libertinus regular's (ɖ's hook) stops at -188.
    Returns (part, the heights of its new seams).
    """
    target = style.path("g").bounds[1]
    delta = part.bounds[1] - target
    if delta <= 0.5:
        return part, []
    # Where the stem's two edges are still straight: the higher of their line ends.
    probe = y_join - 2.5
    x0, x1 = intervals(_segs(part), 0.0, probe)[-1]
    split = math.ceil(max(_straight_end(part, probe, x0, True), _straight_end(part, probe, x1, True))) + 2
    high = min(split + 40.5, y_join - 1.5)
    (a0, a1), (b0, b1) = intervals(_segs(part), 0.0, split + 0.5)[-1], intervals(_segs(part), 0.0, high)[-1]
    ml, mr = (b0 - a0) / (high - split - 0.5), (b1 - a1) / (high - split - 0.5)   # dx/dy of the two edges
    upper = _inter(part, _sbox(-1000, split, 2000, 1000))
    lower = _inter(part, _sbox(-1000, -1000, 2000, split))
    m = (ml + mr) / 2
    lower = _moved(lower, (1, 0, 0, 1, -delta * m, -delta))
    band = _poly([(a0, split), (a1, split), (a1 - delta * mr, split - delta), (a0 - delta * ml, split - delta)], 0.0)
    return _union(upper, band, lower), [split, split - delta]


def draft_q_hook(style, base="q", base_path=None, deep=False):
    path, y_join, note = graft(style, base, "ɖ", Q_JOIN, _q_tail_cut(), _q_tail_cut(), -1, -1, base_path,
                               adjust=_deepen if deep else None)
    if deep:
        note += f"; tail run down to {path.bounds[1]:.0f} (g's depth)"
        OVERLAYS[(("q" if base_path is None else "Ɋ") + " rev", style.key)] = _LAST_DONOR[0]
        JOINS[(("q" if base_path is None else "Ɋ") + " rev", style.key)] = y_join
    else:
        JOINS[("ɋ" if base_path is None else "Ɋ", style.key)] = y_join
        OVERLAYS[("ɋ" if base_path is None else "Ɋ", style.key)] = _LAST_DONOR[0]
    d = style.path("ɖ")
    hook_rsb = style.advance("ɖ") - d.bounds[2]
    advance = max(style.advance(base) if base_path is None else 0, path.bounds[2] + hook_rsb)
    return path, round(advance), note


def draft_u_hook(style):
    path, y_join, note = graft(style, "u", "ɿ", 200, _left_stem_top(), _above, 0, 0, down=False)
    JOINS[("ꭒ", style.key)] = y_join
    # The hook is the leftmost ink: regular's ꭒ has ɿ's left sidebearing + 10 (25 vs 15).
    shift = style.path("ɿ").bounds[0] + U_HOOK_LSB - path.bounds[0]
    path = _moved(path, (1, 0, 0, 1, shift, 0))
    return path, round(style.advance("u") + shift), (
        note + f"; moved {shift:+.0f} for ɿ's left sidebearing + {U_HOOK_LSB}")


U_HOOK_LSB = 10


def _straighten(path, tolerance=5.0):
    """Curves whose control points lie within `tolerance` of their chord become lines."""
    out, cur = [], None
    for op, pts in _recording(path):
        if op == "curveTo":
            (ax, ay), (bx, by), (cx, cy) = pts
            dx, dy = cx - cur[0], cy - cur[1]
            n = math.hypot(dx, dy)
            if n > 0 and all(abs(dy * (px - cur[0]) - dx * (py - cur[1])) / n < tolerance
                             for px, py in ((ax, ay), (bx, by))):
                op, pts = "lineTo", (pts[-1],)
        out.append((op, pts))
        if pts:
            cur = pts[-1]
    return _from_recording(out)


def _right_edge(path, y):
    return intervals(_segs(path), 0.0, y)[-1][1]


def _right_arm(style, char):
    """Thickness and dx/dy of y's right arm (the stroke that runs on into the tail), at y 250."""
    p = style.path(char)
    a, b = intervals(_segs(p), 0.0, 250.5)[-1]
    a2, b2 = intervals(_segs(p), 0.0, 310.5)[-1]
    slope = ((a2 + b2) - (a + b)) / 2 / 60
    return (b - a) * math.cos(math.atan(slope)), slope


Y_LOOP_JOIN = -10    # above regular ỿ's loop (it begins at -31), on the plain tail
Y_LOOP_TAPER = 60    # how far below the join the taper reaches into the loop


def _hull(points):
    """Convex hull (monotone chain), counter-clockwise."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def draft_y_loop(dst, src):
    """
    ỿ: dst's y above Y_LOOP_JOIN, src's ỿ below, so that the right edge runs
    straight from y's right arm into the loop's stem, as in regular ỿ (its
    right edge is a line in practice: a curve within 2-4 units of its chord,
    then a line). The loop is slanted to the right arm's own slant, as thick
    relative to the right arm as regular's (about 0.78: loop 28-34, arm 40),
    and placed so that the right edges meet; curves within 5 units of a line
    are straightened, and points left on the straight edge at the join dropped.
    """
    y_join = Y_LOOP_JOIN
    b = dst.path("y")
    t_dst, _ = _right_arm(dst, "y")
    t_src, _ = _right_arm(src, "ỿ")
    # The loop continues the right stroke: its slant is the right edge's just
    # below the join (italic y's right stroke curves, from dx/dy 0.38 at y 250
    # to 0.66 below the baseline), y's and the loop's alike.
    def edge_slope(path, y0, y1):
        return (_right_edge(path, y1) - _right_edge(path, y0)) / (y1 - y0)
    m_dst = edge_slope(dst.path("y"), y_join - 40.5, y_join - 2.5)
    m_src = edge_slope(src.path("ỿ"), y_join - 40.5, y_join - 2.5)
    loop = _inter(src.path("ỿ"), _sbox(-1000, -400, 2000, y_join))
    # Slant: the loop's stem follows the arm's slant.
    loop = _moved(loop, (1, 0, m_dst - m_src, 1, -y_join * (m_dst - m_src), 0))
    ratio = t_dst / t_src
    grow = (ratio - 1) * 31 / 2          # 31: regular ỿ's loop thickness (28 at the bottom, 34 at the side)
    if abs(grow) > 0.25:
        loop = _from_recording(embolden(_recording(loop), grow))
    probe = y_join - 2.5
    loop = _moved(loop, (1, 0, 0, 1, _right_edge(b, probe) - _right_edge(loop, probe), 0))
    l_b = intervals(_segs(b), 0.0, probe)[-1]
    l_l = intervals(_segs(loop), 0.0, probe)[-1]
    # Where y's stroke is wider than the loop's stem at the join, a taper (the
    # convex hull of y's stroke just above the join and the top of the loop
    # just below it) replaces the shelf.
    upper = _inter(b, _sbox(l_b[0] - 5, y_join, l_b[1] + 5, y_join + 12))
    # The loop's points: on its outer contour only, so that nothing touches the counter.
    outer = max(_contours(loop), key=lambda c: abs(c.area))
    outer_path = pathops.Path()
    outer.draw(outer_path.getPen())
    up = {(round(x, 3), round(y, 3)) for seg in _segs(upper) for x, y in seg}
    pts = list(up) + [pt for seg in _segs(outer_path) for pt in seg
                      if y_join - Y_LOOP_TAPER <= pt[1] <= y_join]
    hull = _hull(pts)
    # Keep y's points and the two tangent points on the loop: the rest of the
    # loop's side would be a polyline, inside the loop's own curve anyway.
    n = len(hull)
    keep = [hull[i] for i in range(n)
            if hull[i] in up or hull[i - 1] in up or hull[(i + 1) % n] in up]
    taper = _poly(keep, 0.0)
    # The loop's counter stays whole: the taper must not cut its tip.
    for c in _contours(loop):
        if c.clockwise != max(_contours(loop), key=lambda q: abs(q.area)).clockwise:
            hole = pathops.Path()
            c.draw(hole.getPen())
            taper = _diff(taper, _from_recording(_recording(hole)))
    path = _union(_diff(b, _sbox(-1000, -400, 2000, y_join)), loop, taper)
    path = _merge_straight(_straighten(path), y_join)
    return path, dst.advance("y"), (
        f"{dst.key}'s y above {y_join}, {src.key}'s ỿ below, slanted to y's right edge below the join (dx/dy {m_dst:.3f}"
        f" vs {m_src:.3f}), loop × {ratio:.2f} (right arm {t_dst:.0f} vs {t_src:.0f}), right edges joined;"
        f" stroke at the join {l_b[1] - l_b[0]:.0f} (y) vs {l_l[1] - l_l[0]:.0f} (loop)")


def draft_y_loop_v1(dst, src):
    """dst's y with src's ỿ loop below y_join, matched on the tail at y_join."""
    y_join = -10                # above the loop (regular's starts at -31), on the plain tail
    probe = y_join - 3          # just below the cut, where both tails have ink
    s_src, s_dst = src.slope, dst.slope
    loop = _inter(src.path("ỿ"), _sbox(-1000, -400, 2000, y_join, s_src))
    loop = _moved(loop, (1, 0, s_dst - s_src, 1, -y_join * (s_dst - s_src), 0))
    grow = (_stem_width(dst) - _stem_width(src)) / 2
    if abs(grow) > 0.5:
        loop = _from_recording(embolden(_recording(loop), grow))
    b = dst.path("y")
    b0, b1 = _interval(b, probe, 0.0, -1)
    l0, l1 = _interval(loop, probe, 0.0, -1)
    loop = _moved(loop, (1, 0, 0, 1, (b0 + b1) / 2 - (l0 + l1) / 2, 0))
    path = _union(_diff(b, _sbox(-1000, -400, 2000, y_join, s_dst)), loop)
    return path, dst.advance("y"), (
        f"{dst.key}'s y above {y_join}, {src.key}'s ỿ below"
        + (f" slanted (tan {s_dst - s_src:.3f})" if s_dst != s_src else "")
        + f", pushed outward by {grow:.1f} (half the difference of the stems of I),"
        f" tail centres matched at {probe}; tails there {b1 - b0:.0f} ({dst.key}'s y)"
        f" vs {l1 - l0:.0f} (the loop)")


def _line_through(path, y1, y2, index, side):
    """The straight edge (side 0 left, 1 right) of interval `index`, through y1 and y2: x(y)."""
    a = intervals(_segs(path), 0.0, y1)[index][side]
    b = intervals(_segs(path), 0.0, y2)[index][side]
    return lambda y: a + (b - a) * (y - y1) / (y2 - y1)


def _beside(edge, left, y0=-400, y1=1000, pad=0.0):
    """The region left (or right) of a straight edge x(y), between y0 and y1."""
    if left:
        return _poly([(-1000, y0), (edge(y0) + pad, y0), (edge(y1) + pad, y1), (-1000, y1)], 0.0)
    return _poly([(edge(y0) - pad, y0), (2000, y0), (2000, y1), (edge(y1) - pad, y1)], 0.0)


def _q_notch(style):
    """
    The style's q: its stem's edges (x(y) lines) and its notch, the lowest
    on-curve point of the outline in the stem column near the top, where the
    bowl's arc meets the stem below the spur.
    """
    q = style.path("q")
    e_l = _line_through(q, 200.5, 300.5, -1, 0)
    e_r = _line_through(q, 200.5, 300.5, -1, 1)
    xh = q.bounds[3]
    outer = pathops.Path()
    max(_contours(q), key=lambda c: abs(c.area)).draw(outer.getPen())
    cands = [pts[-1] for op, pts in _recording(outer) if pts
             and xh - 120 < pts[-1][1] < xh - 2 and e_l(pts[-1][1]) - 5 < pts[-1][0] < e_r(pts[-1][1])]
    return q, e_l, e_r, min(cands, key=lambda p: p[1])


def _o_body(style, path):
    """
    Ɋ's body in the other styles, from the style's own letters:

      bowl      the style's O (regular Ɋ's bowl is O's to within 7%, at -3),
                placed so that its leftmost point is the bowl's; right of its
                highest point, its arcs dip smoothly (a quadratic, level at
                the highest point) down into the notch, as regular Ɋ's do
                (its notch is 35 below its top, like q's 32);
      notch     the style's q's stem top from its notch rightwards (the notch,
                spur and rounded corner), moved onto Ɋ's stem, scaled across
                to its width, with its notch as far below O's top as q's is
                below q's top;
      stem      the copy's (regular's Ɋ, slanted and emboldened) below.
    """
    sl = style.slope
    edge = _line_through(path, 300.5, 450.5, -1, 0)
    edge_r = _line_through(path, 300.5, 450.5, -1, 1)
    o = style.path("O")
    o = _moved(o, (1, 0, 0, 1, path.bounds[0] - o.bounds[0], 0))
    o_top = o.bounds[3]

    q, q_l, q_r, (nx, ny) = _q_notch(style)
    h1, h2 = ny - 30.5, ny - 130.5
    k = (edge_r(h1) - edge(h1)) / (q_r(h1) - q_l(h1))
    c1 = (edge(h1) + edge_r(h1)) / 2 - k * (q_l(h1) + q_r(h1)) / 2
    c2 = (edge(h2) + edge_r(h2)) / 2 - k * (q_l(h2) + q_r(h2)) / 2
    cy = (c2 - c1) / (h2 - h1)
    target = o_top - (q.bounds[3] - ny)                  # the notch's height in Ɋ
    dy = target - ny
    # q's notch and what is right of it, across onto Ɋ's stem, up to `target`.
    notch_line = lambda y: nx + (y - ny) * sl
    piece = _inter(q, _inter(_beside(notch_line, False), _sbox(-1000, ny - 40, 2000, 1000)))
    piece = _moved(piece, (k, 0, cy, 1, c1 - cy * h1, 0))
    nx2 = k * nx + c1 + cy * (ny - h1)
    piece = _moved(piece, (1, 0, 0, 1, dy * sl, dy))
    nx2 += dy * sl

    # O's arcs dip from the highest point down into the notch.
    pts = [pt for seg in _segs(o) for pt in seg]
    x_top = max(pts, key=lambda p: p[1])[0]
    arc = max(y for y in range(int(o_top) - 200, int(o_top) + 2)
              if o.contains((nx2, y + 0.5)))
    dip = arc - target
    mid = (o.bounds[1] + o_top) / 2

    def bend(x, y):
        if y <= mid or x <= x_top:
            return y
        u = min(1.0, (x - x_top) / (nx2 - x_top))
        return y - dip * u * u * (y - mid) / (o_top - mid)
    o = _from_recording([(op, tuple((x, bend(x, y)) for x, y in pts)) for op, pts in _recording(o)])

    top_band = _sbox(-1000, target - 15, 2000, 1000)
    notch_in_q = lambda y: nx2 + (y - target) * sl     # the notch's vertical (slanted) in Ɋ
    # At the bottom the ring runs a little into the stem column, so that it
    # meets the hook's curve (as at regular's cusp) rather than ending flat.
    bottom_band = _sbox(-1000, -400, 2000, 40)
    o_part = _inter(o, _union(_beside(edge, True, pad=2),
                              _inter(top_band, _beside(notch_in_q, True, pad=1)),
                              _inter(bottom_band, _beside(edge, True, pad=30))))
    # The copy's stem, above the bowl's bottom only: below, the tail's own
    # stem takes over (`hook_tail` continues it straight; `graft` replaces it).
    stem = _inter(path, _inter(_beside(edge, False, pad=2), _sbox(-1000, 40, 2000, target - 20)))
    body = _union(o_part, stem, piece)
    for seam in (target - 20, target - 40, target - 15):
        body = _merge_straight(body, seam)
    return body


HOOK_DONORS = ("ʈ", "ɽ")   # the hooks whose stem runs straight closest to their bottom


def hook_tail(style, base_path, stem_y, straight_top, base_name, donors=None, deep=True, key=None,
              cut=True):
    """
    A hook tail down to the descender (g's depth), grafted on a straight stem.

    The base's stem edges are the lines through stem_y (two heights where the
    stem is straight); the stem is continued along them as far as needed. The
    donor is the first of HOOK_DONORS whose hook, moved down to g's depth,
    stays straight down to at most `straight_top` (where the base's own
    straight descender begins), so that both edges run straight into the
    hook's curves (ɖ's hook curves from 73-94 down, too high for that).
    donors: the hooks to try (default HOOK_DONORS); deep False keeps the
    donor's own depth. key: the figure key for JOINS and OVERLAYS. cut False:
    the base has no stem below its bowl to remove (Ɋ's body).
    Returns (path, note).
    """
    target = style.path("g").bounds[1]
    e_l = _line_through(base_path, *stem_y, -1, 0)
    e_r = _line_through(base_path, *stem_y, -1, 1)
    for donor in donors or HOOK_DONORS:
        d = style.path(donor)
        dy = target - d.bounds[1] if deep else 0.0
        d = _moved(d, (1, 0, 0, 1, 0, dy))
        idx = 0 if donor in ("ʈ", "ɽ") else -1
        probe = 150.5 + dy
        x0, x1 = intervals(_segs(d), 0.0, probe)[idx]
        y_j = max(_straight_end(d, probe, x0, True), _straight_end(d, probe, x1, True))
        if y_j <= straight_top:
            break
    y_j = math.ceil(y_j)
    # Align the donor's stem (lines through y_j + 2.5 and y_j + 40.5) on the base's.
    h1, h2 = y_j + 2.5, y_j + 40.5
    (d0, d1), (D0, D1) = intervals(_segs(d), 0.0, h1)[idx], intervals(_segs(d), 0.0, h2)[idx]
    b0, b1, B0, B1 = e_l(h1), e_r(h1), e_l(h2), e_r(h2)
    k = (b1 - b0) / (d1 - d0)
    c1 = (b0 + b1) / 2 - k * (d0 + d1) / 2
    c2 = (B0 + B1) / 2 - k * (D0 + D1) / 2
    cy = (c2 - c1) / (h2 - h1)
    # The hook only (the hooks all turn right): right of the donor's stem's
    # left edge, so that ɖ brings no part of d's bowl.
    d_l = lambda y: d0 + (D0 - d0) * (y - h1) / (h2 - h1)
    part = _inter(d, _inter(_sbox(-1000, -400, 2000, y_j + 20), _beside(d_l, False, pad=2)))
    matrix = (k, 0, cy, 1, c1 - cy * h1, 0)
    part = _moved(part, matrix)
    # The base: its old tail goes (below y_j, and all of the stem column below
    # the stem's top); the stem runs on straight, from above the bowl's bottom
    # down to the hook.
    top = max(70, y_j + 10)
    cut_region = _union(_sbox(-1000, -400, 2000, min(y_j, -14)),
                        _inter(_beside(e_l, False, pad=-2), _sbox(-1000, -400, 2000, top - 10)))
    band = _poly([(e_l(top), top), (e_r(top), top), (e_r(y_j - 1), y_j - 1), (e_l(y_j - 1), y_j - 1)], 0.0)
    path = _union(_diff(base_path, cut_region) if cut else base_path, band, part)
    for seam in (y_j, y_j - 1, top, top - 10, -14):
        path = _merge_straight(path, seam)
    key = key or base_name + " rev"
    JOINS[(key, style.key)] = y_j
    OVERLAYS[(key, style.key)] = _moved(d, matrix)
    return path, (f"tail: {style.key}'s {donor} hook, moved down {-dy:.0f} to g's depth ({target:.0f}),"
                  f" on {base_name}'s stem continued straight down to y {y_j} (× {k:.2f} across)")


def draft_q_tail(style):
    """ɋ revision: the style's q with its own straight descender run into a hook at g's depth."""
    q = style.path("q")
    a, _ = intervals(_segs(q), 0.0, -50.5)[-1]
    top = _straight_end(q, -50.5, a, False)
    path, note = hook_tail(style, q, (-40.5, -90.5), top, "q")
    d = style.path("ɖ")
    advance = max(style.advance("q"), path.bounds[2] + style.advance("ɖ") - d.bounds[2])
    return path, round(advance), f"{style.key}'s q, own descender; " + note


def draft_Q_tail(style, src):
    """Ɋ revision: the Ɋ body (designer's in regular, else O's bowl + regular's stem) with a hook tail."""
    if style.has("Ɋ"):
        # Regular: the version reviewed as good on 2026-11-13, the designer's Ɋ
        # with ɖ's hook lengthened to g's depth.
        path, advance, note = draft_q_hook(style, base="Ɋ", base_path=style.path("Ɋ"), deep=True)
        return path, style.advance("Ɋ"), f"{style.key}'s Ɋ; " + note
    # The other styles: only the stem lengthens; the hook and its ball are ɖ's.
    path, advance, note = draft_Q_hook(style, src, deep=True)
    return path, advance, note


def draft_Q_hook(dst, src, deep=False):
    """
    Ɋ: src's Ɋ (copied to dst), its bowl and notch from dst's O and q, with
    dst's ɖ hook as tail on the stem continued straight (`hook_tail`): at ɖ's
    own depth, or (deep) moved down to g's, only the stem lengthening.
    """
    body, advance, note = copied(dst, src, "Ɋ")
    body = _o_body(dst, body)
    note += "; bowl and notch from own O and q"
    if deep:
        path, note2 = hook_tail(dst, body, (300.5, 450.5), 1e9, "Ɋ", donors=("ɖ",), key="Ɋ rev", cut=False)
        d = dst.path("ɖ")
        advance2 = path.bounds[2] + dst.advance("ɖ") - d.bounds[2]
    else:
        path, advance2, note2 = draft_q_hook(dst, base="Ɋ", base_path=body)
    return path, max(advance, advance2), note + "; " + note2


def _crossbar_band(style, glyph="J"):
    """
    (y0, y1) of the crossbar across the stem of the italic J (None if it has
    none): the heights between 150 and 480 where the ink is wider than the
    stem by more than 4 units.
    """
    path, sl = style.path(glyph), style.slope
    rows = []
    for y in [150.5 + 2 * i for i in range(165)]:
        iv = intervals(_segs(path), sl, y)
        if len(iv) == 1:
            rows.append((y, iv[0][1] - iv[0][0]))
    stem = statistics.median(w for _, w in rows)
    wide = [y for y, w in rows if w > stem + 4]
    return (min(wide) - 2, max(wide) + 2) if wide else None


def _poly(points, slope):
    """A polygon from points in sheared coordinates."""
    p = pathops.Path()
    (x, y), rest = points[0], points[1:]
    p.moveTo(x + y * slope, y)
    for x, y in rest:
        p.lineTo(x + y * slope, y)
    p.close()
    return p


def j_without_crossbar(style):
    """
    The style's J with the crossbar across its stem cut away (italic and
    semibold italic J have one, about 28 units thick, below the middle; the
    tilde-like stroke at the top stays). The cut follows the stem's edges,
    taken as straight from just below the bar to just above it; points left
    on a straight edge are dropped.
    """
    j, sl = style.path("J"), style.slope
    band = _crossbar_band(style)
    if band is None:
        return j
    y0, y1 = band
    (l0, r0), (l1, r1) = intervals(_segs(j), sl, y0 - 4)[0], intervals(_segs(j), sl, y1 + 4)[0]

    def edge(a, b, y):    # the stem edge at y, straight from (a, y0 - 4) to (b, y1 + 4)
        return a + (b - a) * (y - (y0 - 4)) / ((y1 + 4) - (y0 - 4))

    left = _poly([(-1000, y0), (edge(l0, l1, y0), y0), (edge(l0, l1, y1), y1), (-1000, y1)], sl)
    right = _poly([(edge(r0, r1, y0), y0), (2000, y0), (2000, y1), (edge(r0, r1, y1), y1)], sl)
    out = _diff(j, _union(left, right))
    return _merge_straight(_merge_straight(out, y0), y1)


def draft_J_bar(style):
    """
    Ɉ in the italics: the style's J without its own crossbar (the tilde-like
    top stroke stays), with a capital bar where the crossbar was.
    """
    s = style.slope
    y0, y1 = _crossbar_band(style)
    yc = (y0 + y1) / 2
    j = j_without_crossbar(style)
    t = _bar_thickness(style, "Đ", "D")
    s0, s1 = _interval(j, yc, s, 0)
    bar = _sbox(s0 - J_BAR_OVERHANG[0], yc - t / 2, s1 + J_BAR_OVERHANG[1], yc + t / 2, s)
    path = _union(j, bar)
    jj = style.path("J")
    advance = style.advance("J") + max(0, path.bounds[2] - jj.bounds[2])
    return path, advance, (
        f"{style.key}'s J without its own crossbar ({y0:.0f}-{y1:.0f}, cut along the stem), with a bar"
        f" {t:.0f} thick (own Đ) at its centre, y {yc:.0f}, overhanging the stem {J_BAR_OVERHANG[0]}"
        f" left and {J_BAR_OVERHANG[1]} right (regular Ɉ's)")


def draft_J_bar_ij(style):
    """Ɉ, second rejected candidate: the J of the style's Ĳ (no flag) with a capital bar."""
    s = style.slope
    ij = style.path("Ĳ")
    (_, i1), (j0, _) = intervals(_segs(ij), s, 620)[:2]
    split = (i1 + j0) / 2
    j = _inter(ij, _union(_sbox(split, -5, 2000, 1000, s), _sbox(-1000, -400, 2000, -5, s)))
    a0, a1 = _interval(j, 310, s, 0)
    b0, b1 = _interval(style.path("J"), 310, s, 0)
    j = _moved(j, (1, 0, 0, 1, (b0 + b1 - a0 - a1) / 2, 0))
    t = _bar_thickness(style, "Đ", "D")
    s0, s1 = _interval(j, J_BAR_Y, s, 0)
    bar = _sbox(s0 - J_BAR_OVERHANG[0], J_BAR_Y - t / 2, s1 + J_BAR_OVERHANG[1], J_BAR_Y + t / 2, s)
    path = _union(j, bar)
    advance = style.advance("J") + max(0, path.bounds[2] - style.path("J").bounds[2])
    return path, advance, "the J of Ĳ with a capital bar at the middle"


# Regular Ɇ is regular E with the combining long solidus overlay U+0338 over
# it, moved right 610 (the stroke's ends are U+0338's to the unit): the
# solidus crosses half E's height 23 units left of E's centre.
SOLIDUS_OFFSET = -23.0

# The long solidus U+0338 of semibold and semibold italic is the short one
# (it spans -28..454, U+0337's size): redrawn as the matching style's, moved
# as that style's U+0337 is (semibold's U+0337 is regular's to the unit;
# semibold italic's is italic's moved right 12, as stage 3 copies italic marks).
LONG_SOLIDUS_SOURCE = {"semibold": ("regular", 0), "semibold_italic": ("italic", 12)}


def _long_solidus(style, styles):
    """The style's long solidus U+0338 (redrawn for semibold and semibold italic). Returns (path, note)."""
    if style.key in LONG_SOLIDUS_SOURCE:
        src, dx = LONG_SOLIDUS_SOURCE[style.key]
        return _moved(styles[src].path("\u0338"), (1, 0, 0, 1, dx, 0)), f"U+0338 redrawn from {src}'s"
    return style.path("\u0338"), f"{style.key}'s U+0338"


def _de_slanted_centre(path, slope, y):
    """The middle of a glyph at height y: the centre of its de-slanted bounding box, at y."""
    xs = [x - yy * slope for seg in _segs(path) for x, yy in seg]
    return (min(xs) + max(xs)) / 2 + y * slope


def _placed_solidus(style, styles):
    """
    The long solidus over the style's E: its centreline crosses half E's
    height SOLIDUS_OFFSET left of E's middle there (the de-slanted centre,
    so that in the italics the middle follows the slant).
    """
    sol, src = _long_solidus(style, styles)
    e = style.path("E")
    ym = (e.bounds[1] + e.bounds[3]) / 2
    a, b = intervals(_segs(sol), 0.0, ym)[0]
    dx = _de_slanted_centre(e, style.slope, ym) + SOLIDUS_OFFSET - (a + b) / 2
    return _moved(sol, (1, 0, 0, 1, dx, 0)), src


def draft_E_solidus(style, styles):
    """Ɇ: the style's E with the long solidus U+0338 over it, as regular's Ɇ is built."""
    sol, src = _placed_solidus(style, styles)
    path = _union(style.path("E"), sol)
    t = _shape(sol)[2]
    return path, style.advance("E"), (
        f"{style.key}'s E + {src} (long solidus overlay, {t:.0f} thick), crossing half E's height"
        f" {-SOLIDUS_OFFSET:.0f} left of E's de-slanted centre, as in regular Ɇ")


def _solidus_axis(sol):
    """Centre, unit direction (up the stroke), length and thickness of a straight stroke."""
    pts = [pt for _, operands in _recording(sol) for pt in operands]
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    area, length, thick = _shape(sol)
    x0, y0, x1, y1 = sol.bounds
    ux, uy = (x1 - x0), (y1 - y0)
    n = math.hypot(ux, uy)
    return (cx, cy), (ux / n, uy / n), length, thick


def draft_E_rectangle(style, styles, sheared=False):
    """
    Ɇ variants on the solidus's centreline and thickness: a plain rectangle
    (ends square to the stroke), or (sheared) a parallelogram with level ends,
    as Ⱥ's stroke has, from the solidus's lowest to its highest point.
    """
    sol, src = _placed_solidus(style, styles)
    (cx, cy), (ux, uy), length, t = _solidus_axis(sol)
    if sheared:
        y0, y1 = sol.bounds[1], sol.bounds[3]
        w = t / uy                                       # horizontal width of the stroke
        xb = cx + (y0 - cy) * ux / uy
        xt = cx + (y1 - cy) * ux / uy
        quad = [(xb - w / 2, y0), (xb + w / 2, y0), (xt + w / 2, y1), (xt - w / 2, y1)]
    else:
        nx, ny = -uy, ux
        hl, ht = length / 2, t / 2
        quad = [(cx - ux * hl - nx * ht, cy - uy * hl - ny * ht), (cx - ux * hl + nx * ht, cy - uy * hl + ny * ht),
                (cx + ux * hl + nx * ht, cy + uy * hl + ny * ht), (cx + ux * hl - nx * ht, cy + uy * hl - ny * ht)]
    stroke_contour = [(quad[i], quad[(i + 1) % 4]) for i in range(4)]
    if gc.signed_area(stroke_contour) < 0:
        stroke_contour = gc.reverse(stroke_contour)
    return _cs(style, "E") + [stroke_contour], style.advance("E"), "variant"


def draft_LL(dst, src):
    """Ỻ: dst's I and L with a baseline bar joining their stems."""
    dx_src = _fit_dx(src.path("Ỻ"), lambda x: _union(src.path("I"), src.path("L", x)), range(200, 300))
    dx = round(dx_src * dst.advance("I") / src.advance("I"))
    i, l = dst.path("I"), dst.path("L", dx)
    s = dst.slope
    # The foot's thickness: L's arm, measured upward at the middle of the arm.
    x_arm = (_interval(l, 300, s, 0)[1] + 300 * s + l.bounds[2]) / 2
    t = next(y for y in range(5, 200) if not l.contains((x_arm, y)))
    xa = sum(_interval(i, t / 2, s, 0)) / 2 + t / 2 * s
    xb = sum(_interval(l, t / 2, s, 0)) / 2 + t / 2 * s
    bar = _sbox(xa, 0, xb, t, 0)
    advance = dx + dst.advance("L") + (src.advance("Ỻ") - dx_src - src.advance("L"))
    return _union(i, l, bar), advance, (
        f"{dst.key}'s I + L at {dx:+d} ({src.key}'s at {dx_src:+d}, × I's advance), "
        f"bar along the baseline {t} thick (L's foot) from stem to stem")


# ============================================================
# Constructions (rebuilt 2026-11-13): components, not boolean operations
# ============================================================
#
# Every draft is built the way a font source builds a glyph: the base letter's
# own contours (a reference, under a plain transform), plus a part that is
# either a glyph of the font (an overlay mark U+0335-U+0338, a turned or moved
# letter) or one simple contour taken once from the designer's own glyph; or a
# splice of two contours, cut where they cross a line and joined there. The
# drafts keep the components' own points and overlap where the components
# overlap (font generation merges them). Boolean operations are used only to
# measure (fits, mismatches) and to take a part out of a designer's glyph once.
#
# In regular the designer built most of these letters the same way (fits by
# translation, ink mismatch): Ɇ = E + U+0338 (0.2%), ɇ = e + U+0337 (0.3%),
# Ƚ = L + U+0336 (0.2%), Ɍ = R + U+0335 (1.1%), ẝ = ſ + U+0335 (1.5%),
# Ɨ = I + U+0335, ƚ = l + U+0335, Đ đ = D d + U+0335, Ɉ = J + U+0336 (3.2%),
# ꞓ = c + U+0335 (4.2%), Ħ Ɏ = H Y + U+0336 (4.5%, 5.5%).


def _cs(style, char, matrix=(1, 0, 0, 1, 0, 0)):
    """The style's glyph as contours (decomposed), transformed."""
    return gc.contours_of(style.glyphs, style.name(char), matrix)


def _as_path(contours):
    """Contours as one pathops path, overlaps resolved: for measuring only."""
    p = pathops.Path()
    gc.draw(contours, p.getPen())
    return pathops.simplify(p, keep_starting_points=False)


def _path_contours(path):
    """A pathops path's contours (no boolean operation: its own points)."""
    return gc._from_recording(_recording(path))


def _ref_x(style, base_path, ref, y):
    """
    Where a part is placed across, at height y: "centre", the base's
    de-slanted centre; ("stem", i), the middle of its i-th ink interval;
    "pair", halfway between the middles of its first two intervals.
    """
    if ref == "centre":
        return _de_slanted_centre(base_path, style.slope, y)
    pairs = intervals(_segs(base_path), 0.0, y)
    if ref == "pair":
        return (sum(pairs[0]) + sum(pairs[1])) / 4
    return sum(pairs[ref[1]]) / 2


# ---------- bars: the base and a stroke overlay mark ----------

# char: (base letters [(letter, dx)], overlay mark, reference, the style's own
# analogous stroke for its thickness)
BAR_SPECS = {
    "Ɍ": ([("R", 0)], "̵", ("stem", 0), ("Đ", "D")),
    "Ɏ": ([("Y", 0)], "̶", "centre", ("Ƚ", "L")),
    "ɏ": ([("y", 0)], "̶", "centre", ("đ", "d")),
    "Ɉ": ([("J", 50)], "̶", ("stem", 0), ("Đ", "D")),
    "ẝ": ([("ſ", 0)], "̵", ("stem", 0), ("đ", "d")),
    "ꞓ": ([("c", 85)], "̵", "centre", ("đ", "d")),
    "ỻ": ([("l", 10), ("l", "advance")], "̶", "pair", ("đ", "d")),
}
_FITS = {}


def _base_parts(style, spec):
    """The base letters of a spec, placed: [(letter, dx)] with "advance" for the first's advance."""
    return [(b, style.advance(spec[0][0]) if dx == "advance" else dx) for b, dx in spec]


def _mark_box(path):
    x0, y0, x1, y1 = path.bounds
    return (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0


def _fit_bar(src, char):
    """
    The overlay mark's placement in src's own glyph: its centre (cx, cy) and
    scale (sx, sy), fitted to the designer's glyph by least ink mismatch
    (coordinate descent). Returns ((cx, cy, sx, sy), mismatch).
    """
    key = (src.key, char)
    if key in _FITS:
        return _FITS[key]
    bases, mark, _, _ = BAR_SPECS[char]
    d = src.path(char)
    b = _union(*(src.path(l, dx) for l, dx in _base_parts(src, bases)))
    m = src.path(mark)
    mcx, mcy, _, _ = _mark_box(m)
    add = _diff(d, b)
    ab = add.bounds
    p = [(ab[0] + ab[2]) / 2, (ab[1] + ab[3]) / 2, 1.0, 1.0]

    def err(q):
        cx, cy, sx, sy = q
        return _xor_ratio(_union(b, _moved(m, (sx, 0, 0, sy, cx - sx * mcx, cy - sy * mcy))), d)
    e = err(p)
    steps = [16.0, 16.0, 0.2, 0.2]
    for _ in range(6):
        for i in range(4):
            for sign in (1, -1):
                while True:
                    q = list(p)
                    q[i] += sign * steps[i]
                    if q[2] <= 0.1 or q[3] <= 0.1:
                        break
                    e2 = err(q)
                    if e2 < e - 1e-6:
                        p, e = q, e2
                    else:
                        break
        steps = [s / 2 for s in steps]
    _FITS[key] = (p, e)
    return p, e


def draft_bar(style, styles, char, src_key="regular", base_contours=None, base_path=None):
    """
    A letter that is its base with a stroke overlay mark (U+0335 or U+0336)
    across it. The mark's placement in the designer's glyph (fitted in
    src_key's style) gives the rule: its centre's height, its offset across
    from the reference (a stem's middle, or the base's de-slanted centre)
    at that height, and the bar's length; the thickness is the fitted one
    scaled by the style's own analogous stroke (Đ, Ƚ, đ) against src's. The
    style's own mark is scaled to that length and thickness. base_contours,
    base_path: a base other than the plain letters (J without its crossbar).
    """
    bases, mark, ref, tref = BAR_SPECS[char]
    src = styles[src_key]
    (cx, cy, sx, sy), fit = _fit_bar(src, char)
    src_base = _union(*(src.path(l, dx) for l, dx in _base_parts(src, bases)))
    offset = cx - _ref_x(src, src_base, ref, cy)
    _, _, w_src, h_src = _mark_box(src.path(mark))
    width = sx * w_src
    thick = sy * h_src * _ref_thickness(style, tref) / _ref_thickness(src, tref)
    m = style.path(mark)
    mcx, mcy, w, h = _mark_box(m)
    placed = _base_parts(style, bases)
    if base_contours is None:
        base_contours = [c for l, dx in placed for c in _cs(style, l, (1, 0, 0, 1, dx, 0))]
        base_path = _union(*(style.path(l, dx) for l, dx in placed))
    x = _ref_x(style, base_path, ref, cy) + offset
    k_x, k_y = width / w, thick / h
    bar = _cs(style, mark, (k_x, 0, 0, k_y, x - k_x * mcx, cy - k_y * mcy))
    if style.has(char):
        advance = style.advance(char)
    else:
        advance = src.advance(char) + sum(style.advance(l) - src.advance(l) for l, _ in bases)
    return base_contours + bar, advance, (
        f"{' + '.join(l for l, _ in bases)} + U+{ord(mark):04X} (the style's own), placed as in {src_key}'s"
        f" {char} (fit {100 * fit:.1f}%): centre at y {cy:.0f}, {offset:+.0f} across from the"
        f" {'de-slanted centre' if ref == 'centre' else 'stems' if ref == 'pair' else 'stem'}, {width:.0f} long,"
        f" {thick:.0f} thick (own {tref[0]})")


# ---------- parts taken once from the designer's glyph ----------

def _hull_polygon(points, tol=1.5):
    hull = _hull(points)
    segs = gc.merge_lines([(hull[i], hull[(i + 1) % len(hull)]) for i in range(len(hull))], tol)
    return segs


def _part(src, char, base, base_dx, convex):
    """
    The part a designer's letter adds to its base, as one contour: the pieces
    of the glyph outside the base, with the base's ink between them (the
    stroke's middle, across the stem). convex: a straight stroke, taken as
    the convex hull of the pieces (ẜ's is a rectangle); else the pieces
    joined through the base inside their hull (ꝥ's swelling ends kept).
    Returns contours.
    """
    d, b = src.path(char), src.path(base, base_dx)
    pieces = [c for c in _contours(_diff(d, b)) if abs(c.area) > MIN_PIECE]
    pts = [p for c in pieces for seg in _segs(c) for p in seg]
    hull = _hull_polygon(pts)
    if convex:
        return [hull]
    hp = _as_path([hull])
    whole = _union(*pieces, _inter(b, hp))
    return [gc.merge_lines(c, 0.5) for c in _path_contours(whole)]


PART_SPECS = {
    # char: (base, base dx, convex, the style's own analogous stroke, reference)
    "ẜ": ("ſ", 0, True, ("ɇ", "e"), ("stem", 0)),
    "ꝥ": ("þ", 30, False, ("đ", "d"), ("stem", 0)),
}


def draft_part(style, styles, char, src_key="regular"):
    """
    The base with a part taken from src's glyph: placed at the same height and
    offset across from the stem, slanted to the style's angle about its own
    centre, thickened as the style's own analogous stroke is thicker.
    """
    base, bdx, convex, tref, ref = PART_SPECS[char]
    src = styles[src_key]
    part = _part(src, char, base, bdx, convex)
    x0, y0, x1, y1 = gc.bounds(part)
    cy = (y0 + y1) / 2
    src_path = _as_path(part)
    cx = _de_slanted_centre(src_path, src.slope, cy)
    offset = cx - _ref_x(src, src.path(base, bdx), ref, cy)
    shear = style.slope - src.slope
    part = gc.transform(part, (1, 0, shear, 1, -shear * cy, 0))
    ratio = _ref_thickness(style, tref) / _ref_thickness(src, tref)
    thickness = _shape(_as_path(part))[2]
    grow = (ratio - 1) * thickness / 2
    if abs(grow) > 0.25:
        rec = []
        for c in part:
            sub = []
            gc.draw([c], _ListPen(sub))
            rec += embolden(sub, grow)
        part = gc._from_recording(rec)
    base_path = style.path(base, bdx)
    x = _ref_x(style, base_path, ref, cy) + offset
    now = _de_slanted_centre(_as_path(part), style.slope, cy)
    part = gc.transform(part, (1, 0, 0, 1, x - now, 0))
    advance = style.advance(base) + src.advance(char) - src.advance(base)
    return _cs(style, base, (1, 0, 0, 1, bdx, 0)) + part, advance, (
        f"{style.key}'s {base} + {src_key}'s {char} stroke as one contour"
        f" ({gc.on_curve_count(part)} points), {offset:+.0f} across from the stem at y {cy:.0f},"
        + (f" slanted (tan {shear:.3f})," if shear else "") + f" × {ratio:.2f} thick (own {tref[0]})")


class _ListPen:
    """A pen recording into a list (moveTo/lineTo/curveTo/closePath tuples)."""

    def __init__(self, out):
        self.out = out

    def moveTo(self, p):
        self.out.append(("moveTo", (p,)))

    def lineTo(self, p):
        self.out.append(("lineTo", (p,)))

    def curveTo(self, *pts):
        self.out.append(("curveTo", pts))

    def closePath(self):
        self.out.append(("closePath", ()))


# ---------- references ----------

def draft_E_solidus_c(style, styles):
    """Ɇ: the style's E and its long solidus U+0338, as regular's Ɇ is built."""
    sol, src = _placed_solidus(style, styles)
    return _cs(style, "E") + _path_contours(sol), style.advance("E"), (
        f"{style.key}'s E + {src} (long solidus overlay), crossing half E's height"
        f" {-SOLIDUS_OFFSET:.0f} left of E's de-slanted centre, as in regular Ɇ")


def turned_c(style, letter):
    path, w, note = turned(style, letter)
    return _path_contours(path), w, note


def draft_LL_c(style, styles):
    """Ỻ: the style's I and L as they are, and one bar contour along the baseline between their stems."""
    src = styles["regular"]
    dx_src = _fit_dx(src.path("Ỻ"), lambda x: _union(src.path("I"), src.path("L", x)), range(200, 300))
    dx = round(dx_src * style.advance("I") / src.advance("I"))
    i, l = style.path("I"), style.path("L", dx)
    s = style.slope
    x_arm = (_interval(l, 300, s, 0)[1] + 300 * s + l.bounds[2]) / 2
    t = next(y for y in range(5, 200) if not l.contains((x_arm, y)))
    xa = sum(_interval(i, t / 2, s, 0)) / 2 + t / 2 * s
    xb = sum(_interval(l, t / 2, s, 0)) / 2 + t / 2 * s
    bar = [[((xa, 0), (xb, 0)), ((xb, 0), (xb, t)), ((xb, t), (xa, t)), ((xa, t), (xa, 0))]]
    advance = dx + style.advance("L") + (src.advance("Ỻ") - dx_src - src.advance("L"))
    return _cs(style, "I") + _cs(style, "L", (1, 0, 0, 1, dx, 0)) + bar, advance, (
        f"{style.key}'s I + L at {dx:+d} (regular's at {dx_src:+d}, × I's advance), and a bar"
        f" {t} thick (L's foot) from stem to stem along the baseline: three overlapping contours")


# ---------- splices ----------

def _outer(contours):
    """The index of the largest contour (the outline, as opposed to counters)."""
    return max(range(len(contours)), key=lambda i: abs(gc.signed_area(contours[i])))


def _stem_align(base_path, b_idx, donor_path, d_idx, h1, h2):
    """
    The transform that puts the donor's stem (interval d_idx) on the base's
    (interval b_idx): centre lines through h1 and h2, scaled across to the
    base's width at h1. x' = k x + cy y + c.
    """
    (b0, b1), (d0, d1) = intervals(_segs(base_path), 0.0, h1)[b_idx], intervals(_segs(donor_path), 0.0, h1)[d_idx]
    (B0, B1), (D0, D1) = intervals(_segs(base_path), 0.0, h2)[b_idx], intervals(_segs(donor_path), 0.0, h2)[d_idx]
    k = (b1 - b0) / (d1 - d0)
    c1 = (b0 + b1) / 2 - k * (d0 + d1) / 2
    c2 = (B0 + B1) / 2 - k * (D0 + D1) / 2
    cy = (c2 - c1) / (h2 - h1)
    return (k, 0, cy, 1, c1 - cy * h1, 0), k


def _splice_at(base_cs, donor_cs, y, b_idx, d_idx, keep_base_above, donor_y=None):
    """
    Splice the base's outline and the donor's at height y (the donor's own
    at donor_y), where interval b_idx of the base and d_idx of the donor
    cross it; the base's other contours kept, the donor's kept if they lie
    wholly on its kept side. Points left on a straight edge at the join are
    dropped.
    """
    donor_y = y if donor_y is None else donor_y
    bo, do = _outer(base_cs), _outer(donor_cs)
    bp, dp = _as_path([base_cs[bo]]), _as_path([donor_cs[do]])
    probe_b = y + (0.5 if keep_base_above else -0.5)
    probe_d = donor_y + (-0.5 if keep_base_above else 0.5)
    ba = intervals(_segs(bp), 0.0, probe_b)[b_idx]
    da = intervals(_segs(dp), 0.0, probe_d)[d_idx]
    spliced = gc.splice(base_cs[bo], donor_cs[do], gc.horizontal(y), ba, da,
                        keep_base_left=keep_base_above, donor_line=gc.horizontal(donor_y))
    near = lambda p: min(abs(p[1] - y), abs(p[1] - donor_y)) < 1.5
    spliced = gc.merge_lines(spliced, 1.5, near)
    others = [c for i, c in enumerate(base_cs) if i != bo]
    for i, c in enumerate(donor_cs):
        if i == do:
            continue
        _, cy0, _, cy1 = gc.bounds([c])
        if (keep_base_above and cy1 < donor_y) or (not keep_base_above and cy0 > donor_y):
            others.append(c)
    return [spliced] + others


def _join_height(base_path, b_idx, donor_path, d_idx, probe=250.5, down=True, cap=None):
    """Where both stems' straight edges end (see `graft`), capped below a crossbar."""
    ends = []
    for path, index in ((base_path, b_idx), (donor_path, d_idx)):
        x0, x1 = intervals(_segs(path), 0.0, probe)[index]
        ends += [_straight_end(path, probe, x0, down), _straight_end(path, probe, x1, down)]
    y = math.ceil(max(ends)) if down else math.floor(min(ends))
    return min(y, cap) if cap is not None else y


def draft_M_hook_c(style):
    """Ɱ: M spliced with J's hook where both stems are straight; the leg runs straight into the hook."""
    m_path, j_path = style.path("M"), style.path("J")
    band = _crossbar_band(style)
    y = _join_height(m_path, -1, j_path, 0, cap=None if band is None else math.floor(band[0]) - 3)
    matrix, k = _stem_align(m_path, -1, j_path, 0, y + 2.5, y + (60.5 if band else 100.5))
    donor = _cs(style, "J", matrix)
    out = _splice_at(_cs(style, "M"), donor, y, -1, 0, True)
    JOINS[("Ɱ", style.key)] = y
    OVERLAYS[("Ɱ", style.key)] = _as_path(donor)
    return out, style.advance("M"), f"{style.key}'s M spliced with J's hook at y {y}, stem × {k:.2f} across"


def draft_u_hook_c(style):
    """ꭒ: u spliced with ɿ's fishhook at y 200 (u's left stem)."""
    u_path, r_path = style.path("u"), style.path("ɿ")
    y = 200
    matrix, k = _stem_align(u_path, 0, r_path, 0, y - 2.5, y - 100.5)
    donor = _cs(style, "ɿ", matrix)
    out = _splice_at(_cs(style, "u"), donor, y, 0, 0, keep_base_above=False)
    shift = r_path.bounds[0] + U_HOOK_LSB - gc.bounds(out)[0]
    out = gc.transform(out, (1, 0, 0, 1, shift, 0))
    JOINS[("ꭒ", style.key)] = y
    OVERLAYS[("ꭒ", style.key)] = _moved(_as_path(donor), (1, 0, 0, 1, shift, 0))
    return out, round(style.advance("u") + shift), (
        f"{style.key}'s u spliced with ɿ's fishhook at y {y}, stem × {k:.2f};"
        f" moved {shift:+.0f} for ɿ's left sidebearing + {U_HOOK_LSB}")


def draft_q_tail_c(style):
    """
    ɋ: q's own straight descender spliced with a hook (ʈ's, or regular ɽ's)
    moved down to g's depth, where both are straight (`hook_tail`'s choice).
    """
    q = style.path("q")
    a, _ = intervals(_segs(q), 0.0, -50.5)[-1]
    top = _straight_end(q, -50.5, a, False)
    target = style.path("g").bounds[1]
    for donor in HOOK_DONORS:
        d = style.path(donor)
        dy = target - d.bounds[1]
        d = _moved(d, (1, 0, 0, 1, 0, dy))
        probe = 150.5 + dy
        x0, x1 = intervals(_segs(d), 0.0, probe)[0]
        y = math.ceil(max(_straight_end(d, probe, x0, True), _straight_end(d, probe, x1, True)))
        if y <= top:
            break
    y = min(y, math.floor(top) - 2)
    # The donor's stem on q's descender (lines through -40.5 and -90.5, extended).
    e_l = _line_through(q, -40.5, -90.5, -1, 0)
    e_r = _line_through(q, -40.5, -90.5, -1, 1)
    h1, h2 = y + 2.5, y + 40.5
    (d0, d1), (D0, D1) = intervals(_segs(d), 0.0, h1)[0], intervals(_segs(d), 0.0, h2)[0]
    k = (e_r(h1) - e_l(h1)) / (d1 - d0)  # noqa
    c1 = (e_l(h1) + e_r(h1)) / 2 - k * (d0 + d1) / 2
    c2 = (e_l(h2) + e_r(h2)) / 2 - k * (D0 + D1) / 2
    cy = (c2 - c1) / (h2 - h1)
    hook = _cs(style, donor, (k, 0, cy, 1, c1 - cy * h1, dy))
    out = _splice_at(_cs(style, "q"), hook, y, -1, 0, True)
    JOINS[("ɋ", style.key)] = y
    OVERLAYS[("ɋ", style.key)] = _as_path(hook)
    advance = style.advance("q") + 8          # regular ɋ: q's + 8
    return out, advance, (
        f"{style.key}'s q spliced at y {y} (its own straight descender) with {donor}'s"
        f" hook moved down {-dy:.0f} to g's depth ({target:.0f}), stem × {k:.2f}")


def _q_body_c(style, styles):
    """
    Ɋ's body: regular's Ɋ (slanted, pushed outward) with its bowl spliced from
    the style's own O, cut 3 units left of the stem's left edge: outline and
    counter each spliced, O's arcs dipped so that its outer arc crosses the
    cut where the copy's does (regular's arc dips into the notch). In
    regular, the designer's own.
    """
    if style.has("Ɋ"):
        return _cs(style, "Ɋ"), style.advance("Ɋ"), f"{style.key}'s Ɋ"
    copy, advance, note = copied(style, styles["regular"], "Ɋ")
    cc = _path_contours(copy)
    edge = _line_through(copy, 300.5, 450.5, -1, 0)
    sl = (edge(1000) - edge(0)) / 1000
    line = gc.slanted(edge(0) - 3, sl)
    o = style.path("O")
    o = _moved(o, (1, 0, 0, 1, copy.bounds[0] - o.bounds[0], 0))
    oc = _path_contours(o)
    # Where the copy's outline crosses the cut at the top.
    co = _outer(cc)
    top_c = max(gc.crossings(cc[co], line), key=lambda c: c[2][1])[2]
    o_top = o.bounds[3]
    mid = (o.bounds[1] + o_top) / 2
    pts = [p for seg in _segs(o) for p in seg]
    x_top = max(pts, key=lambda p: p[1])[0]

    def bent(dip):
        def bend(p):
            x, y = p
            if y <= mid or x <= x_top:
                return p
            u = min(1.0, (x - x_top) / (top_c[0] - x_top))
            return (x, y - dip * u * u * (y - mid) / (o_top - mid))
        return [[tuple(bend(p) for p in seg) for seg in segs] for segs in oc]

    def top_y(dip):
        b = bent(dip)
        return max(gc.crossings(b[_outer(b)], line), key=lambda c: c[2][1])[2][1]
    lo, hi = -50.0, 200.0
    for _ in range(40):
        midd = (lo + hi) / 2
        if top_y(midd) > top_c[1]:
            lo = midd
        else:
            hi = midd
    ob = bent((lo + hi) / 2)
    oo = _outer(ob)
    oi = [i for i in range(len(ob)) if i != oo][0]
    ci = [i for i in range(len(cc)) if i != co][0]

    def splice_pair(base, donor):
        cb = sorted(gc.crossings(base, line), key=lambda c: c[2][1])
        cd = sorted(gc.crossings(donor, line), key=lambda c: c[2][1])
        targets = (cb[0][2], cb[-1][2])
        dts = (cd[0][2], cd[-1][2])
        s = gc.splice(base, donor, line, targets, dts, keep_base_left=False)
        return s
    outer = splice_pair(cc[co], ob[oo])
    counter = splice_pair(cc[ci], ob[oi])
    return [outer, counter], advance, note + "; bowl spliced from own O (arc dipped into the notch)"


def draft_Q_tail_c(style, styles):
    """
    Ɋ: the body (`_q_body_c`) with its own tail (regular's, ɖ's hook) run
    down to g's depth: the outline is cut just below the bowl and the lower
    part moved down along the stem; the stem's two edges join the parts in
    straight lines. Only the stem lengthens; the hook and its ball are kept.
    """
    body, advance, note = _q_body_c(style, styles)
    bp = _as_path(body)
    target = style.path("g").bounds[1]
    delta = bp.bounds[1] - target
    y = -14.0
    e_l = _line_through(bp, 300.5, 450.5, -1, 0)
    e_r = _line_through(bp, 300.5, 450.5, -1, 1)
    m = ((e_l(450.5) + e_r(450.5)) - (e_l(300.5) + e_r(300.5))) / 2 / 150
    lower = gc.transform(body, (1, 0, 0, 1, -delta * m, -delta))
    out = _splice_at(body, lower, y, -1, -1, True, donor_y=y - delta)
    JOINS[("Ɋ", style.key)] = y
    return out, advance, note + f"; tail lengthened by {delta:.0f} below y {y:.0f} (stem only)"


def draft_y_loop_c(dst, src):
    """
    ỿ: y spliced at Y_LOOP_JOIN with src's ỿ below, slanted to y's right
    edge just below the join and weighted by the right arm (as draft_y_loop),
    right edges meeting; on the left the donor is cut 30 lower, so that the
    join is a taper rather than a shelf.
    """
    y_join = Y_LOOP_JOIN
    t_dst, _ = _right_arm(dst, "y")
    t_src, _ = _right_arm(src, "ỿ")

    def edge_slope(path, y0, y1):
        return (_right_edge(path, y1) - _right_edge(path, y0)) / (y1 - y0)
    m_dst = edge_slope(dst.path("y"), y_join - 40.5, y_join - 2.5)
    m_src = edge_slope(src.path("ỿ"), y_join - 40.5, y_join - 2.5)
    loop = _cs(src, "ỿ", (1, 0, m_dst - m_src, 1, -y_join * (m_dst - m_src), 0))
    grow = (t_dst / t_src - 1) * 31 / 2
    if abs(grow) > 0.25:
        rec = []
        for c in loop:
            sub = []
            gc.draw([c], _ListPen(sub))
            rec += embolden(sub, grow)
        loop = gc._from_recording(rec)
    probe = y_join - 2.5
    shift = _right_edge(dst.path("y"), probe) - _right_edge(_as_path(loop), probe)
    loop = gc.transform(loop, (1, 0, 0, 1, shift, 0))
    out = _splice_at(_cs(dst, "y"), loop, y_join, -1, -1, True)
    JOINS[("ỿ", dst.key)] = y_join
    return out, dst.advance("y"), (
        f"{dst.key}'s y spliced at y {y_join} with {src.key}'s ỿ below, slanted to y's right edge"
        f" (dx/dy {m_dst:.3f} vs {m_src:.3f}), loop × {t_dst / t_src:.2f} (right arm)")


def draft_J_nobar(style):
    """Italic J with its own crossbar spliced out: below the bar and above it, joined along the stem's edges."""
    j = _cs(style, "J")
    band = _crossbar_band(style)
    if band is None:
        return j
    y0, y1 = band
    return _splice_at(j, j, y0 - 2, 0, 0, keep_base_above=False, donor_y=y1 + 2)


def draft_J_bar_c(style, styles):
    """Ɉ in the italics: J without its crossbar (the tilde stroke kept), with U+0336 across the stem."""
    jn = draft_J_nobar(style)
    jp = _as_path(jn)
    contours, advance, note = draft_bar(style, styles, "Ɉ", base_contours=gc.transform(jn, (1, 0, 0, 1, 50, 0)),
                                        base_path=_moved(jp, (1, 0, 0, 1, 50, 0)))
    return contours, advance, "J without its own crossbar (spliced out); " + note


# Each entry: char, label, the styles to draft (None: those that lack it),
# and a function (dst style, styles dict) -> (path, advance, note).
def _src(styles, dst, italic_source=None):
    return styles["italic"] if italic_source and dst.key == "semibold_italic" else styles["regular"]


CAP_BAR = ("Đ", "D")
CAP_BAR_L = ("Ƚ", "L")      # regular Ɏ's bar is Ƚ's thickness (44), Đ's is 40
LC_BAR = ("đ", "d")
DIAGONAL = ("ɇ", "e")
CAP_DIAGONAL = ("Ø", "O")   # regular Ɇ's stroke is Ø's (47 and 48 at 51°); ɇ's is 39
DIAGONALS = {"ɇ", "Ø"}

# Ɉ in the italics. Libertinus italic J has a calligraphic flag at its top (an
# arm running left from the stem and turning down, like italic T's arms), so a
# bar through it reads as a second stroke. The italic Ĳ has the designer's own
# J without the flag (I-like serifs at the top): Ɉ is that J with a capital
# bar, as thick as the style's Đ bar, overhanging the stem as much as regular
# Ɉ's (118 left, 113 right), at the middle of the capital height, where Gentium
# Plus (roman, italic and bold italic: 300-344 of 615) and Noto Serif italic
# put it; regular's is at 0.39 (230-274).
J_BAR_Y = 0.52 * 647
J_BAR_OVERHANG = (118, 113)

LETTERS = [
    ("Ɇ", "reference", lambda d, S: draft_E_solidus_c(d, S)),
    ("Ɍ", "overlay", lambda d, S: draft_bar(d, S, "Ɍ")),
    ("Ɏ", "overlay", lambda d, S: draft_bar(d, S, "Ɏ")),
    ("ɏ", "overlay", lambda d, S: draft_bar(d, S, "ɏ")),
    ("Ɉ", "splice + overlay", lambda d, S: draft_J_bar_c(d, S)),
    # From regular in both styles: italic's ẜ is drawn afresh (not ſ + stroke),
    # so its difference from ſ is slivers, not the stroke.
    ("ẜ", "part", lambda d, S: draft_part(d, S, "ẜ")),
    ("ẝ", "overlay", lambda d, S: draft_bar(d, S, "ẝ", "italic" if d.key == "semibold_italic" else "regular")),
    ("ꝥ", "part", lambda d, S: draft_part(d, S, "ꝥ")),
    ("ꞓ", "overlay", lambda d, S: draft_bar(d, S, "ꞓ")),
    ("Ɱ", "splice", lambda d, S: draft_M_hook_c(d)),
    ("ꭒ", "splice", lambda d, S: draft_u_hook_c(d)),
    ("ỿ", "splice", lambda d, S: draft_y_loop_c(d, S["regular"])),
    ("Ɋ", "splice", lambda d, S: draft_Q_tail_c(d, S)),
    ("Ỻ", "reference", lambda d, S: draft_LL_c(d, S)),
    ("Ⅎ", "turn", lambda d, S: turned_c(d, "F")),
]

# Not in the base groups: the lowercase partners of Ɋ and Ỻ, and the other
# turned capitals, which also exist only in regular.
EXTRAS = [
    ("ɋ", "splice", lambda d, S: draft_q_tail_c(d)),
    ("ỻ", "overlay", lambda d, S: draft_bar(d, S, "ỻ")),
    ("Ɐ", "turn", lambda d, S: turned_c(d, "A")),
    ("Ʌ", "turn", lambda d, S: turned_c(d, "V")),
]

# The reviewer's decisions on the drafts (2026-11-13), shown on the sheet.
# The reviewer's decisions on the drafts, shown on the sheet: (state, note).
# States: approved; changed (approved, but the draft changed since); pending
# (tentative, or revised and not yet reviewed); rejected.
REBUILT = "rebuilt 2026-11-13 from components (references, overlapping contours, splices)"
DECISIONS = {
    "Ɇ": ("pending", "E + the long solidus U+0338 (as regular's Ɇ); middle anchor moved right in the italics"),
    "Ɍ": ("changed", f"approved 2026-11-13; {REBUILT}: R + U+0335"),
    "Ɏ": ("changed", f"approved 2026-11-13; {REBUILT}: Y + U+0336"),
    "ɏ": ("changed", f"approved 2026-11-13 (italic's spikes since); {REBUILT}: y + U+0336"),
    "Ɉ": ("changed", f"approved 2026-11-13; {REBUILT}: J, its crossbar spliced out, + U+0336"),
    "ẜ": ("changed", f"approved 2026-11-13; {REBUILT}: ſ + the stroke of regular's ẜ as one contour"),
    "ẝ": ("changed", f"approved 2026-11-13; {REBUILT}: ſ + U+0335"),
    "ꝥ": ("changed", f"approved 2026-11-13; {REBUILT}: þ + regular's stroke as one contour"),
    "ꞓ": ("changed", f"approved 2026-11-13; {REBUILT}: c + U+0335"),
    "Ɱ": ("changed", f"approved 2026-11-13; {REBUILT}: M and J spliced"),
    "ꭒ": ("changed", f"approved 2026-11-13; {REBUILT}: u and ɿ spliced"),
    "ỿ": ("pending", f"{REBUILT}: y and regular's ỿ spliced"),
    "Ɋ": ("pending", f"{REBUILT}: regular's Ɋ, bowl spliced from O, tail lengthened (stem only)"),
    "Ỻ": ("pending", f"rejected 2026-11-13; {REBUILT}: I, L and a bar contour"),
    "Ⅎ": ("approved", "2026-11-13 (a turned reference)"),
    "ɋ": ("pending", f"{REBUILT}: q's own descender spliced with a hook at the descender"),
    "ỻ": ("changed", f"approved 2026-11-13; {REBUILT}: l + l + U+0336"),
    "Ɐ": ("approved", "2026-11-13 (a turned reference)"),
    "Ʌ": ("approved", "2026-11-13 (a turned reference)"),
}
SECTIONS = [
    ("approved", "Approved", "Approved on 2026-11-13."),
    ("changed", "Approved, but rebuilt since", "Rebuilt from components; to check again (FontForge)."),
    ("pending", "Pending", "Tentative, or redrafted after a comment."),
    ("rejected", "Rejected", ""),
]

# Other candidates for comparison: char -> [(label, recipe)], in the draft
# fonts at VARIANT_PUA[char] + i.
VARIANTS = {
    "Ɇ": [
        ("rectangle: the solidus's centreline and thickness, square ends", lambda d, S: draft_E_rectangle(d, S)),
        ("parallelogram: the same, level ends (as Ⱥ's stroke)", lambda d, S: draft_E_rectangle(d, S, sheared=True)),
    ],
}
VARIANT_PUA = {"Ɇ": 0xF640}

# Revisions of the designer's own regular glyph: char -> (label, recipe), in
# the regular draft font at REVISION_PUA[char].
REVISIONS = {
    "ɋ": ("revision: tail to the descender (g's depth), straight descender", lambda d, S: draft_q_tail_c(d)),
    "Ɋ": ("revision: tail to the descender (g's depth), stem lengthened", lambda d, S: draft_Q_tail_c(d, S)),
}
REVISION_PUA = {"ɋ": 0xF630, "Ɋ": 0xF631}

# Recipes checked in regular against the designer's glyph.
CHECKS = [
    ("Ɇ", lambda S: draft_E_solidus_c(S["regular"], S)),
    ("Ɍ", lambda S: draft_bar(S["regular"], S, "Ɍ")),
    ("Ɏ", lambda S: draft_bar(S["regular"], S, "Ɏ")),
    ("ɏ", lambda S: draft_bar(S["regular"], S, "ɏ")),
    ("Ɉ", lambda S: draft_bar(S["regular"], S, "Ɉ")),
    ("ẝ", lambda S: draft_bar(S["regular"], S, "ẝ")),
    ("ꞓ", lambda S: draft_bar(S["regular"], S, "ꞓ")),
    ("ỻ", lambda S: draft_bar(S["regular"], S, "ỻ")),
    ("ẜ", lambda S: draft_part(S["regular"], S, "ẜ")),
    ("ꝥ", lambda S: draft_part(S["regular"], S, "ꝥ")),
    ("Ɱ", lambda S: draft_M_hook_c(S["regular"])),
    ("ꭒ", lambda S: draft_u_hook_c(S["regular"])),
    ("Ỻ", lambda S: draft_LL_c(S["regular"], S)),
    ("Ⅎ", lambda S: turned_c(S["regular"], "F")),
    ("Ɐ", lambda S: turned_c(S["regular"], "A")),
    ("Ʌ", lambda S: turned_c(S["regular"], "V")),
]
CHECK_PUA = 0xF600


# ------------------------------------------------------------
# Writing glyphs
# ------------------------------------------------------------

MIN_CONTOUR = 400   # units²: smaller contours are slivers of the boolean operations


def _set_mark_outline(ttfont, glyph_name, path):
    """Replace a mark's outline (zero advance; its anchors and GDEF class unchanged)."""
    top = ttfont["CFF "].cff.topDictIndex[0]
    private = top.Private
    width = None if private.defaultWidthX == 0 else 0 - private.nominalWidthX
    pen = T2CharStringPen(width, None)
    path.draw(pen)
    top.CharStrings[glyph_name] = pen.getCharString(private=private, globalSubrs=top.GlobalSubrs)
    ttfont["hmtx"].metrics[glyph_name] = (0, round(path.bounds[0]))


def _despike(path, tol=0.6):
    """
    Drop zero-length segments and spikes (a line out and straight back along
    itself) that boolean operations leave where two edges coincide.
    """
    out = []
    for contour in path.contours:
        segs = [(op, pts) for op, pts in _recording(contour) if op in ("moveTo", "lineTo", "curveTo")]
        start = segs[0][1][0]
        steps = [(op, pts) for op, pts in segs[1:]]
        changed = True
        while changed and len(steps) > 2:
            changed = False
            n = len(steps)
            ends = [start] + [st[1][-1] for st in steps]
            for i in range(n):
                a, b = ends[i], ends[i + 1]
                degenerate_curve = (steps[i][0] == "curveTo" and math.dist(a, b) < tol
                                    and all(math.dist(a, c) < 3 * tol for c in steps[i][1][:2]))
                if (steps[i][0] == "lineTo" and math.dist(a, b) < tol) or degenerate_curve:
                    del steps[i]
                    changed = True
                    break
                if i + 1 < n and math.dist(ends[i], ends[i + 2]) < tol:   # out and back (lines or curves)
                    del steps[i:i + 2]
                    changed = True
                    break
        if len(steps) < 2:
            continue
        out.append(("moveTo", (start,)))
        out.extend(steps)
        out.append(("closePath", ()))
    return _from_recording(out)





def _add_glyph(ttfont, glyph_name, codepoint, path, advance):
    top = ttfont["CFF "].cff.topDictIndex[0]
    charstrings = top.CharStrings
    private = top.Private
    advance = round(advance)
    width = None if advance == private.defaultWidthX else advance - private.nominalWidthX
    pen = T2CharStringPen(width, None)
    if isinstance(path, list):
        # A construction: its contours as they are, overlapping (no merge).
        gc.draw(path, pen)
        lsb = gc.bounds(path)[0]
    else:
        rounded = pathops.Path()
        for contour in _despike(path).contours:
            if abs(contour.area) >= MIN_CONTOUR:
                contour.draw(rounded.getPen())
        rounded.draw(pen)
        lsb = path.bounds[0]
    charstring = pen.getCharString(private=private, globalSubrs=top.GlobalSubrs)
    if glyph_name in charstrings.charStrings:
        charstrings[glyph_name] = charstring
    else:
        order = ttfont.getGlyphOrder()
        order.append(glyph_name)
        ttfont.setGlyphOrder(order)
        if top.charset is not order and glyph_name not in top.charset:
            top.charset.append(glyph_name)
        charstrings.charStrings[glyph_name] = len(charstrings.charStringsIndex)
        charstrings.charStringsIndex.append(charstring)
    ttfont["hmtx"].metrics[glyph_name] = (advance, round(lsb))
    gdef = ttfont["GDEF"].table
    if gdef.GlyphClassDef is not None:
        gdef.GlyphClassDef.classDefs[glyph_name] = 1   # base
    for table in ttfont["cmap"].tables:
        if table.isUnicode():
            table.cmap[codepoint] = glyph_name


def build_drafts():
    """
    Draft every missing letter, write fonts/*-draft.otf, and return the
    notes: {char: {style: note}}, the checks [(char, xor ratio, note)], and
    {char: {style: "designer" | "draft"}}.
    """
    styles = {key: Style(key) for key in ORDER}
    # The recipes read the unmodified patched fonts; drafts go into copies.
    out = {key: TTFont(FONTS_DIR / f"{STYLES[key]}-patch.otf") for key in ORDER}
    notes, status = {}, {}
    for char, kind, recipe in LETTERS + EXTRAS:
        notes[char], status[char] = {}, {}
        for key in ORDER:
            style = styles[key]
            if style.has(char):
                status[char][key] = "designer"
                continue
            path, advance, note = recipe(style, styles)
            _add_glyph(out[key], f"uni{ord(char):04X}", ord(char), path, advance)
            notes[char][key] = f"[{kind}] {note}; advance {round(advance)}"
            status[char][key] = "draft"

    # The long solidus U+0338, redrawn where it is the short one.
    for key in LONG_SOLIDUS_SOURCE:
        path, _ = _long_solidus(styles[key], styles)
        _set_mark_outline(out[key], styles[key].name("\u0338"), path)

    # Revisions of the designer's own glyphs.
    for char, (label, recipe) in REVISIONS.items():
        for key in ORDER:
            if status[char][key] != "designer":
                continue
            path, advance, note = recipe(styles[key], styles)
            _add_glyph(out[key], f"uni{ord(char):04X}.rev", REVISION_PUA[char], path, advance)
            notes[char][key + "_rev"] = f"[revision] {note}; advance {round(advance)}"

    # Earlier (rejected) candidates, for comparison on the sheet.
    for char, entries in VARIANTS.items():
        for i, (label, recipe) in enumerate(entries):
            for key in ORDER:
                if status[char][key] != "draft":
                    continue
                path, advance, _ = recipe(styles[key], styles)
                _add_glyph(out[key], f"uni{ord(char):04X}.v{i + 1}", VARIANT_PUA[char] + i, path, advance)

    checks = []
    for i, (char, recipe) in enumerate(CHECKS):
        regular = styles["regular"]
        path, advance, note = recipe(styles)
        measured = _as_path(path) if isinstance(path, list) else path
        designer = regular.path(char)
        ratio = _xor_ratio(measured, designer)
        shifted, shift = min((_xor_ratio(_moved(measured, (1, 0, 0, 1, dx, 0)), designer), dx)
                             for dx in range(-40, 41))
        _add_glyph(out["regular"], f"uni{ord(char):04X}.recipe", CHECK_PUA + i, path, advance)
        checks.append((char, CHECK_PUA + i, ratio, shifted, shift, advance, regular.advance(char), note))

    for key in ORDER:
        out[key].save(FONTS_DIR / f"{STYLES[key]}-draft.otf")
    return notes, checks, status


# ------------------------------------------------------------
# Turned letters: turned or redrawn?
# ------------------------------------------------------------

TURNED_PAIRS = [("a", "ɐ"), ("e", "ǝ"), ("h", "ɥ"), ("k", "ʞ"), ("m", "ɯ"), ("r", "ɹ"),
                ("t", "ʇ"), ("v", "ʌ"), ("w", "ʍ"), ("y", "ʎ"), ("F", "Ⅎ"), ("A", "Ɐ"), ("V", "Ʌ")]
TURNED_EXACT = 0.02   # ink XOR over ink: below this the letter is its base turned


def turn_fit(ttfont, base, turned_char):
    """
    Ink XOR over ink of the turned letter against its base letter turned 180°,
    centred across and aligned at the top, middle or bottom, whichever fits
    best (a turned h or k may have a shorter stem); None if the font lacks
    either. Close to 0: the designer turned the base letter; well above:
    redrew it.
    """
    cmap = ttfont.getBestCmap()
    if ord(base) not in cmap or ord(turned_char) not in cmap:
        return None
    gs = ttfont.getGlyphSet()
    t = _path(gs, cmap[ord(turned_char)])
    b = _path(gs, cmap[ord(base)], (-1, 0, 0, -1, 0, 0))
    tb, bb = t.bounds, b.bounds
    dx = (tb[0] + tb[2] - bb[0] - bb[2]) / 2
    return min(
        _xor_ratio(_moved(b, (1, 0, 0, 1, dx, dy)), t)
        for dy in (tb[1] - bb[1], (tb[1] + tb[3] - bb[1] - bb[3]) / 2, tb[3] - bb[3])
    )


def _verdict(ratio):
    if ratio < TURNED_EXACT:
        return r"\textbf{t}"
    return f"{min(100 * ratio, 99):.0f}\\,\\%" if ratio < 1 else r"$>$99\,\%"


# ------------------------------------------------------------
# The test sheet
# ------------------------------------------------------------

SHEET = TEX_DIR / "missing_glyphs_test_sheet.tex"

# Comparison fonts: family command, label, files per style.
COMPARE = [
    ("Gentium", "Gentium Plus", ["GentiumPlus-Regular.ttf", "GentiumPlus-Italic.ttf",
                                  "GentiumPlus-Bold.ttf", "GentiumPlus-BoldItalic.ttf"]),
    ("Noto", "Noto Serif", ["NotoSerif-Regular.ttf", "NotoSerif-Italic.ttf",
                            "NotoSerif-Bold.ttf", "NotoSerif-BoldItalic.ttf"]),
    ("Junicode", "Junicode Two Beta", ["JunicodeTwoBeta-Regular.otf", "JunicodeTwoBeta-Italic.otf",
                                       "JunicodeTwoBeta-Bold.otf", "JunicodeTwoBeta-BoldItalic.otf"]),
]
SHAPE = {"regular": r"\upshape\mdseries", "italic": r"\itshape\mdseries",
         "semibold": r"\upshape\bfseries", "semibold_italic": r"\itshape\bfseries"}
LABEL = {"regular": "Regular", "italic": "Italic", "semibold": "Semibold",
         "semibold_italic": "Semibold italic"}

# What each cell shows: the base letter, the letter, and a letter with the
# analogous part in the same style.
CONTEXT = {
    "Ɇ": "EɆØ", "Ɍ": "RɌĐ", "Ɏ": "YɎȽ", "ɏ": "yɏđ", "Ɉ": "JɈĐ", "ẜ": "ſẜɇ", "ẝ": "ſẝđ",
    "ꝥ": "þꝥđ", "ꞓ": "cꞓđ", "Ɱ": "MⱮJ", "ꭒ": "uꭒɿ", "ỿ": "yỿ", "Ɋ": "QɊɖ", "Ỻ": "LỺI",
    "Ⅎ": "FℲ", "ɋ": "qɋɖ", "ỻ": "lỻł", "Ɐ": "AⱯ", "Ʌ": "VɅ",
}


def _tex(text):
    return (text.replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("&", r"\&")
            .replace("%", r"\%").replace("#", r"\#"))


def _chars(text, target=None, draft=False):
    out = []
    for ch in text:
        cell = f'\\char"{ord(ch):04X}'
        if ch == target and draft:
            cell = f"\\textcolor{{draft}}{{{cell}}}"
        out.append(cell)
    return "".join(out)


def _cell(family, key, text, target, cmap, draft=False, size=30):
    shown = "".join(ch if ord(ch) in cmap else "" for ch in text)
    missing = ord(target) not in cmap
    body = _chars(shown, target, draft) + (r"\,{\normalsize\color{gray}--}" if missing else "")
    return f"{{\\{family}{SHAPE[key]}\\fontsize{{{size}}}{{{size + 6}}}\\selectfont {body}}}"


# char, joining height, cm per unit (Ɱ larger, two to a row).
# char, joining height where not in JOINS, cm per unit (Ɱ larger, two to a row).
# Underneath (light grey): "donor", the donor glyph as its graft placed it;
# "y", the style's y at the same origin.
GRAFT_FIGURES = [("Ɱ", None, 0.0098, "donor"), ("ꭒ", None, 0.0055, "donor"),
                 ("ɋ", None, 0.0055, "donor"), ("ɋ", "rev", 0.0055, "donor"),
                 ("Ɋ", None, 0.0055, None), ("Ɋ", "rev", 0.0055, None),
                 ("ỿ", None, 0.0055, "y"),
                 ("Ỻ", None, 0.0046, None), ("Ɇ", None, 0.0055, None),
                 ("Ɍ", None, 0.0055, None), ("Ɏ", None, 0.0055, None), ("ɏ", None, 0.0055, None),
                 ("Ɉ", None, 0.0055, None), ("ẜ", None, 0.0055, None), ("ẝ", None, 0.0055, None),
                 ("ꝥ", None, 0.0055, None), ("ꞓ", None, 0.0055, None), ("ỻ", None, 0.0055, None)]


def _tikz_under(path, k):
    """A path drawn underneath, light grey, with its on-curve points."""
    cmds, dots = [], []
    for op, pts in _recording(path):
        if op == "moveTo":
            cmds.append(f"({pts[0][0] * k:.3f},{pts[0][1] * k:.3f})")
            dots.append(pts[0])
        elif op == "lineTo":
            cmds.append(f"-- ({pts[0][0] * k:.3f},{pts[0][1] * k:.3f})")
            dots.append(pts[0])
        elif op == "curveTo":
            a, b, c = pts
            cmds.append(f".. controls ({a[0] * k:.3f},{a[1] * k:.3f}) and ({b[0] * k:.3f},{b[1] * k:.3f})"
                        f" .. ({c[0] * k:.3f},{c[1] * k:.3f})")
            dots.append(c)
        elif op == "closePath":
            cmds.append("-- cycle")
    out = [f"\\fill[gray!10, nonzero rule] {' '.join(cmds)};",
           f"\\draw[gray!55, line width=0.3pt] {' '.join(cmds)};"]
    out += [f"\\fill[gray!55] ({x * k:.3f},{y * k:.3f}) circle (0.4pt);" for x, y in dots]
    return out


def _tikz_points(glyphs, name, y_join, label, k, under=None):
    """
    A tikz picture of a glyph's outline with its on- and off-curve points (k:
    cm per unit); `under`, a path drawn underneath in light grey.
    """
    pen = RecordingPen()
    glyphs[name].draw(pen)
    right = (glyphs[name].width + 30) * k
    path, dots, handles = [], [], []
    cur = None
    for op, pts in pen.value:
        if op == "moveTo":
            cur = pts[0]
            path.append(f"({cur[0] * k:.3f},{cur[1] * k:.3f})")
            dots.append(cur)
        elif op == "lineTo":
            cur = pts[0]
            path.append(f"-- ({cur[0] * k:.3f},{cur[1] * k:.3f})")
            dots.append(cur)
        elif op == "curveTo":
            a, b, c = pts
            path.append(f".. controls ({a[0] * k:.3f},{a[1] * k:.3f}) and ({b[0] * k:.3f},{b[1] * k:.3f})"
                        f" .. ({c[0] * k:.3f},{c[1] * k:.3f})")
            handles += [(cur, a), (c, b)]
            dots.append(c)
            cur = c
        elif op in ("closePath", "endPath"):
            path.append("-- cycle")
    on = len(dots)
    out = [r"\begin{tikzpicture}[baseline=0pt]"] + (_tikz_under(under, k) if under is not None else []) + [
           f"\\fill[gray!18, nonzero rule, fill opacity=0.75] {' '.join(path)};",
           f"\\draw[black!70, line width=0.25pt] {' '.join(path)};",
           (f"\\draw[red!60, dashed, line width=0.3pt] (-0.2,{y_join * k:.3f}) -- ({right:.3f},{y_join * k:.3f});"
            if y_join is not None else ""),
           f"\\draw[gray!50, line width=0.2pt] (-0.2,0) -- ({right:.3f},0);"]
    for (x0, y0), (x1, y1) in handles:
        out.append(f"\\draw[draft!60, line width=0.2pt] ({x0 * k:.3f},{y0 * k:.3f}) -- ({x1 * k:.3f},{y1 * k:.3f});"
                   f"\\draw[draft, line width=0.2pt, fill=white] ({x1 * k:.3f},{y1 * k:.3f}) circle (0.35pt);")
    for x, y in dots:
        out.append(f"\\fill ({x * k:.3f},{y * k:.3f}) circle (0.45pt);")
    out.append(f"\\node[anchor=north west, font=\\scriptsize, inner sep=0pt] at (0,{-270 * k:.3f}) {{{label}: {on} on-curve points}};")
    out.append(r"\end{tikzpicture}\hfill")
    return "\n".join(out)


def write_sheet(notes, checks, status):
    drafts = {key: TTFont(FONTS_DIR / f"{STYLES[key]}-draft.otf") for key in ORDER}
    lib = {key: drafts[key].getBestCmap() for key in ORDER}
    orig = {key: TTFont(FONTS_DIR / f"{STYLES[key]}.otf") for key in ORDER}
    compare = {
        fam: [TTFont(FONTS_DIR / f) for f in files] for fam, _, files in COMPARE
    }
    cmaps = {fam: [f.getBestCmap() for f in fonts] for fam, fonts in compare.items()}

    L = []
    w = L.append
    w("% Generated by run_missing_glyphs_sheet.py (missing_glyphs.py); do not edit.")
    w(r"\documentclass[10pt]{article}")
    w(r"\usepackage[table]{xcolor}")
    w(r"\usepackage{fontspec}")
    w(r"\usepackage{longtable}")
    w(r"\usepackage{tikz}")
    w(r"\usepackage{geometry}")
    w(r"\geometry{a4paper, left=1.2cm, right=1.2cm, top=1.3cm, bottom=1.3cm}")
    w(r"\setlength{\parindent}{0pt}")
    w(r"\definecolor{draft}{RGB}{20,70,190}")
    w(r"\setmainfont{Libertinus Serif}[Path = ../fonts/, UprightFont = LibertinusSerif-Regular.otf,"
      r" ItalicFont = LibertinusSerif-Italic.otf, BoldFont = LibertinusSerif-Semibold.otf,"
      r" BoldItalicFont = LibertinusSerif-SemiboldItalic.otf]")
    w(r"\newfontfamily\LibDraft[Path = ../fonts/, UprightFont = LibertinusSerif-Regular-draft.otf,"
      r" ItalicFont = LibertinusSerif-Italic-draft.otf, BoldFont = LibertinusSerif-Semibold-draft.otf,"
      r" BoldItalicFont = LibertinusSerif-SemiboldItalic-draft.otf]{Libertinus Serif Draft}")
    for fam, label, files in COMPARE:
        w(f"\\newfontfamily\\{fam}[Path = ../fonts/, UprightFont = {files[0]}, ItalicFont = {files[1]},"
          f" BoldFont = {files[2]}, BoldItalicFont = {files[3]}]{{{label}}}")
    w(r"\begin{document}")
    w(r"\section*{Test sheet: drafts of the letters missing in the non-regular styles}")
    w(r"To-do item: ``Create the glyphs that are missing in the non-regular styles because the base groups"
      r" now reach further than the designer's coverage (Ɇ Ɍ Ɏ ɏ ꝥ ꞓ Ɱ ꭒ ỿ exist only in regular,"
      r" Ɉ ẜ ẝ not in every style, and Ɋ Ỻ Ⅎ before them), as stage 2 already does for a few.''"
      r" BASE\_IPA has no gaps; these 15 letters of BASE\_LATIN are all.")
    w("")
    w(r"\smallskip Drafts are in \textcolor{draft}{blue}; black is the designer's glyph."
      r" The drafts are in \verb|fonts/*-draft.otf| (the patched fonts plus the drafts; no anchors),"
      r" written by \verb|run_missing_glyphs_sheet.py|; the recipes are in \verb|missing_glyphs.py|."
      r" Each letter is drafted from the style's own letters where the regular glyph shows how the designer built it:")
    w(r"\begin{description}\setlength\itemsep{0pt}\small")
    w(r"\item[Method (rebuilt 2026-11-13)] Every draft is built from components, as a font source builds a"
      r" glyph: the base letter's own contours, plus a part that is a glyph of the font or one simple"
      r" contour, or a splice of two contours. No boolean operations: the drafts keep the components'"
      r" own points and \emph{overlap} where the components overlap (FontForge shows them unmerged; font"
      r" generation merges them). In regular the designer built most of these letters the same way:"
      r" Ɇ\,=\,E\,+\,U+0338 (0.2\,\% mismatch), Ɍ\,=\,R\,+\,U+0335, ẝ\,=\,ſ\,+\,U+0335, Ɉ\,=\,J\,+\,U+0336, …")
    w(r"\item[overlay] Ɍ Ɏ ɏ ẝ ꞓ ỻ: the base and the style's own stroke overlay mark (U+0335 or U+0336),"
      r" scaled to the bar's length and the style's bar thickness (own Đ, Ƚ or đ), placed as the mark"
      r" fits in the designer's glyph: its height, and its offset from the stem (or the de-slanted centre).")
    w(r"\item[reference] Ɇ: E and the long solidus U+0338 (redrawn in semibold and semibold italic, where"
      r" it was the short one), crossing half E's height 23 left of E's de-slanted centre."
      r" Ỻ: I, L and a bar contour. Ⅎ Ɐ Ʌ: turned references.")
    w(r"\item[part] ẜ ꝥ: the base and the stroke of regular's glyph as one contour (ẜ's a rectangle,"
      r" ꝥ's with its swelling ends), slanted and thickened to the style.")
    w(r"\item[splice] Ɱ (M and J's hook), ꭒ (u and ɿ's fishhook), ỿ (y and regular's ỿ loop),"
      r" ɋ (q's own descender and ʈ's hook, regular ɽ's, at the descender), Ɉ (italic J, its own crossbar"
      r" spliced out, + U+0336), Ɋ (regular's Ɋ, its bowl spliced from the style's O, its tail lengthened"
      r" by splicing it with itself moved down): the outlines are cut where they cross a line and joined"
      r" there; points left on a straight edge are dropped.")
    w(r"\end{description}")
    w(r"Each cell shows the base letter, the letter, and a letter of the same style with the analogous part."
      r" Comparison rows: Gentium Plus, Noto Serif and Junicode (the medievalist font, for ẜ ẝ ꝥ ỿ Ỻ ỻ Ⅎ);"
      r" Langscitinus is left out because it has exactly Libertinus's gaps. A dash: the font lacks the letter.")

    # Overview
    w(r"\subsection*{All drafts in context}")
    w(r"Each letter after its base letter; the last four are outside the base groups."
      r" The letters follow by decision: approved, approved but changed since, then the general sections"
      r" (control points of the grafts, recipe checks, turned letters), and the pending and rejected"
      r" letters last.\par\smallskip")
    for key in ORDER:
        def pairs(entries):
            return r"\ ".join(
                _chars(CONTEXT[c][0]) + _chars(c, c, status[c][key] == "draft") for c, _, _ in entries)
        w(f"{{\\small {LABEL[key]}}}\\par\\nopagebreak{{\\LibDraft{SHAPE[key]}\\fontsize{{18}}{{24}}\\selectfont "
          + pairs(LETTERS) + r"\quad " + pairs(EXTRAS) + r"}\par\smallskip")

    # Per letter
    import unicodedata
    outside = {c for c, _, _ in EXTRAS}
    def letter_sections(states):
        for state, title, intro in [x for x in SECTIONS if x[0] in states]:
            entries = [e for e in LETTERS + EXTRAS if DECISIONS[e[0]][0] == state]
            if not entries:
                continue
            w(f"\\section*{{{title}}}")
            if intro:
                w(intro + r"\par\medskip")
            for char, kind, _ in entries:
                w(r"\begin{minipage}{\linewidth}")
                w(f"\\subsection*{{{{\\LibDraft {_chars(char)}}}\\ U+{ord(char):04X} {unicodedata.name(char).title()} ({kind})"
                  + (" (outside the base groups)" if char in outside else "")
                  + f"{{\\normalfont\\small\\quad {_tex(DECISIONS[char][1])}}}}}")
                w(r"{\renewcommand{\arraystretch}{1.5}\begin{tabular}{@{}l" + "c" * 4 + "@{}}")
                w(" & " + " & ".join(f"\\small {LABEL[k]}" for k in ORDER) + r"\\\hline")
                cells = [_cell("LibDraft", k, CONTEXT[char], char, lib[k], status[char][k] == "draft")
                         for k in ORDER]
                w(r"\small Libertinus & " + " & ".join(cells) + r"\\")
                for fam, label, _ in COMPARE:
                    cells = [_cell(fam, k, CONTEXT[char], char, cmaps[fam][i]) for i, k in enumerate(ORDER)]
                    w(f"\\small {label} & " + " & ".join(cells) + r"\\")
                if char in REVISIONS:
                    cells = []
                    for k in ORDER:
                        if REVISION_PUA[char] not in lib[k]:
                            cells.append("")
                            continue
                        body = (_chars(CONTEXT[char][0]) + f'\\textcolor{{draft}}{{\\char"{REVISION_PUA[char]:04X}}}'
                                + _chars(CONTEXT[char][2:]))
                        cells.append(f"{{\\LibDraft{SHAPE[k]}\\fontsize{{30}}{{36}}\\selectfont {body}}}")
                    w(f"\\parbox{{2.6cm}}{{\\footnotesize {_tex(REVISIONS[char][0])}}} & "
                      + " & ".join(cells) + r"\\")
                for i, (vlabel, _) in enumerate(VARIANTS.get(char, [])):
                    cells = []
                    for k in ORDER:
                        if status[char][k] == "draft":
                            body = (_chars(CONTEXT[char][0]) + f'\\char"{VARIANT_PUA[char] + i:04X}'
                                    + _chars(CONTEXT[char][2:]))
                            cells.append(f"{{\\LibDraft{SHAPE[k]}\\fontsize{{30}}{{36}}\\selectfont {body}}}")
                        else:
                            cells.append("")
                    w(f"\\parbox{{2.6cm}}{{\\footnotesize {_tex(vlabel)}}} & " + " & ".join(cells) + r"\\")
                w(r"\end{tabular}}\par\smallskip")
                w(r"{\footnotesize")
                for key in ORDER:
                    if key in notes[char]:
                        w(f"\\textit{{{LABEL[key]}}}: {_tex(notes[char][key])}.\\par")
                for key in ORDER:
                    if key + "_rev" in notes[char]:
                        w(f"\\textit{{{LABEL[key]}, revision}}: {_tex(notes[char][key + '_rev'])}.\\par")
                w(r"}")
                w(r"\end{minipage}\par\bigskip")

    letter_sections(("approved", "changed"))

    # Control points of the grafts
    w(r"\section*{Control points of the grafts}")
    w(r"The drafts as compiled into \verb|fonts/*-draft.otf| (what FontForge shows on opening them):"
      r" on-curve points black, off-curve points as open circles on their handles;"
      r" the dashed line is the joining height (on the designer's regular glyph, where the recipe joins when"
      r" it is run in regular). The outlines are the result of a boolean union and cut (skia-pathops);"
      r" at the join, points left on a straight stem are dropped, so a stem runs straight from the base"
      r" letter's line into the donor's, as in regular Ɱ.\par\medskip")
    for char, y_join, k, under_kind in GRAFT_FIGURES:
        revision = y_join == "rev"
        fig_key = char
        under_note = {"donor": r" (underneath, in grey: the donor glyph as the graft placed it)",
                      "y": r" (underneath, in grey: the style's y)"}.get(under_kind, "")
        w(r"\par\begin{minipage}{\linewidth}")
        w(f"{{\\LibDraft {_chars(char)}}}\\ U+{ord(char):04X}"
          + (r" revision: tail to the descender" if revision else "") + under_note + r"\par\nopagebreak")
        for key in ORDER:
            glyphs = drafts[key].getGlyphSet()
            if revision:
                if REVISION_PUA[char] not in drafts[key].getBestCmap():
                    continue
                name = drafts[key].getBestCmap()[REVISION_PUA[char]]
                label = LABEL[key] + " (revision of the designer's)"
                y = JOINS.get((char, key))
            else:
                name = drafts[key].getBestCmap()[ord(char)]
                designer = char not in status or status[char][key] == "designer"
                label = LABEL[key] + (" (designer)" if designer else " (draft)")
                y = JOINS.get((char, key), y_join)
            under = None
            if under_kind == "donor":
                under = OVERLAYS.get((fig_key, key))
            elif under_kind == "y":
                under = _path(glyphs, drafts[key].getBestCmap()[ord("y")])
            w(_tikz_points(glyphs, name, y, label, k, under))
        w(r"\par\bigskip\end{minipage}\par")

    # Checks
    w(r"\section*{Recipe checks in regular}")
    w(r"The recipes that take a part from another letter, run in regular and compared with the designer's glyph"
      r" (in the regular draft font at U+F600 and up)."
      r" Mismatch: the ink of designer XOR recipe, at the same origin, over the designer's ink;"
      r" a shift of the whole letter counts double on a thin letter (once where ink is missing, once where"
      r" it is extra), so the mismatch after the best horizontal shift is given too.\par")
    w(r"\medskip{\renewcommand{\arraystretch}{1.6}\begin{tabular}{@{}lccrrrl@{}}")
    w(r"& designer & recipe & mismatch & best shift & advances & \\\hline")
    for char, pua, ratio, shifted, shift, adv, adv_designer, note in checks:
        cell_d = f"{{\\LibDraft\\fontsize{{34}}{{40}}\\selectfont {_chars(char)}}}"
        cell_r = f"{{\\LibDraft\\fontsize{{34}}{{40}}\\selectfont\\color{{draft}}\\char\"{pua:04X}}}"
        w(f"{_chars(char)} & {cell_d} & {cell_r} & {100 * ratio:.1f}\\,\\% &"
          f" {100 * shifted:.1f}\\,\\% at {shift:+d} & {adv_designer} / {round(adv)} &"
          f" \\parbox{{5.4cm}}{{\\footnotesize {_tex(note)}}}\\\\")
    w(r"\end{tabular}}")

    # Turned letters
    w(r"\section*{Turned letters: turned or redrawn?}")
    w(r"Mismatch of each turned letter against its base letter turned 180° (centred across; aligned at"
      r" the top, middle or bottom, whichever fits best):"
      f" under {100 * TURNED_EXACT:.0f}\\,\\% the letter is its base turned (\\textbf{{t}}); above, it was"
      r" redrawn or adjusted. Libertinus original fonts, then the comparison fonts' Ⅎ Ɐ Ʌ.\par")
    w(r"\medskip{\small\begin{tabular}{@{}l" + "r" * 4 + "@{}}")
    w(" & " + " & ".join(LABEL[k] for k in ORDER) + r"\\\hline")

    def row(label, ttfonts, family, base, t):
        cells = []
        for key, ttfont in zip(ORDER, ttfonts):
            r = turn_fit(ttfont, base, t)
            if r is None:
                cells.append(r"{\color{gray}--}")
            else:
                glyphs = f"{{{family}{SHAPE[key]}\\fontsize{{14}}{{16}}\\selectfont {_chars(base + t)}}}"
                cells.append(f"{glyphs}\\enspace\\makebox[2.4em][r]{{{_verdict(r)}}}")
        w(f"{label} & " + " & ".join(cells) + r"\\")

    for base, t in TURNED_PAIRS:
        row(f"Libertinus {_chars(t)}", [orig[k] for k in ORDER], "", base, t)
    w(r"\hline")
    for fam, label, _ in COMPARE:
        for base, t in TURNED_PAIRS[-3:]:
            row(f"{label} {_chars(t)}", compare[fam], f"\\{fam}", base, t)
    w(r"\end{tabular}}")
    # Tail depths
    w(r"\section*{Depths of q, the hook tails, Q and J}")
    w(r"Lowest point of each letter (units per 1000). Libertinus: the original fonts, then the drafts"
      r" (the designer's glyph where there is one), then the revision of ɋ Ɋ with the tail to g's depth."
      r" The Libertinus descender line is $-232$; g reaches $-238$. Junicode has neither ɋ nor Ɋ.\par\medskip")
    w(r"{\small\begin{tabular}{@{}ll" + "r" * 8 + "@{}}")
    depth_chars = "qgɋɖQɊJj"
    w(r"& & " + " & ".join(f"{{\\LibDraft {_chars(c)}}}" for c in depth_chars) + r"\\\hline")
    for label, fonts, rev in [("Libertinus original", [orig[k] for k in ORDER], False),
                              ("Libertinus draft", [drafts[k] for k in ORDER], False),
                              ("Libertinus revision", [drafts[k] for k in ORDER], True)] + \
                             [(lab, compare[fam], False) for fam, lab, _ in COMPARE]:
        for key, ttfont in zip(ORDER, fonts):
            cmap, gs = ttfont.getBestCmap(), ttfont.getGlyphSet()
            upm = ttfont["head"].unitsPerEm
            cells = []
            for c in depth_chars:
                cp = REVISION_PUA[c] if rev and c in REVISION_PUA else ord(c)
                if cp not in cmap or (rev and c not in REVISION_PUA):
                    cells.append(r"{\color{gray}--}" if cp not in cmap else "")
                    continue
                y = _path(gs, cmap[cp]).bounds[1] * 1000 / upm
                cells.append(f"{y:.0f}")
            w(f"{label} & {LABEL[key]} & " + " & ".join(cells) + r"\\")
        w(r"\hline")
    w(r"\end{tabular}}")

    letter_sections(("pending", "rejected"))
    w(r"\end{document}")
    SHEET.write_text("\n".join(L) + "\n", encoding="utf-8")
    return SHEET
