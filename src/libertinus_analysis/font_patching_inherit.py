# font_patching_inherit.py
"""
Shared code of the anchor stages, above all of the two inheritance stages:
derived letters (stage 8, font_patching_derivedanchors) and precomposed
letters (stage 9, font_patching_precomposed_anchors).

Both stages give a letter its base letter's final anchor, moved by how the
base letter sits inside it. This module holds what they share:

    - access to the mark-to-base lookup's base records (also used by stages
      5 and 6);
    - outline sampling: flattened segments, sampled points, and ink
      intervals at a height in sheared coordinates (x' = x - y tan);
    - the interval fit (fit_intervals), used by fit_base (stages 8 and 9)
      and by stem_shift (stage 8's bottom-tail letters), which differ only
      in the heights they compare and how far the scale may stray from 1.
"""

from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables

from .fontmetrics_helpers import SHIFT_K, SLOPE

# ------------------------------------------------------------
# Mark-to-base base records
# ------------------------------------------------------------

def find_mark_to_base_subtables(ttfont, lookup_index):
    """
    Return list of MarkToBase subtables (LookupType 4) for the given lookup_index.
    """
    gpos = ttfont["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]
    return [sub for sub in lookup.SubTable if sub.LookupType == 4]


def get_base_record_for_glyph(sub, glyph_name):
    """
    Return (BaseRecord, index) for glyph_name in this MarkToBase subtable,
    or (None, None) if not present.
    """
    base_cov = sub.BaseCoverage
    base_array = sub.BaseArray

    if glyph_name in base_cov.glyphs:
        idx = base_cov.glyphs.index(glyph_name)
        return base_array.BaseRecord[idx], idx

    return None, None

def ensure_base_record_for_glyph(sub, glyph_name):
    """
    Ensure glyph_name has a BaseRecord in this MarkToBase subtable.
    Return (BaseRecord, index).
    """
    base_cov = sub.BaseCoverage
    base_array = sub.BaseArray
    class_count = sub.ClassCount

    baserec, idx = get_base_record_for_glyph(sub, glyph_name)
    if baserec is not None:
        # Ensure BaseAnchor list matches ClassCount
        while len(baserec.BaseAnchor) < class_count:
            baserec.BaseAnchor.append(None)
        return baserec, idx

    # Create new BaseRecord
    base_cov.glyphs.append(glyph_name)
    baserec = otTables.BaseRecord()
    baserec.BaseAnchor = [None] * class_count
    base_array.BaseRecord.append(baserec)
    idx = len(base_array.BaseRecord) - 1

    return baserec, idx

def get_anchor_from_baserec(baserec, class_index):
    """
    Return (x, y) for BaseAnchor[class_index] in this BaseRecord, or None.
    """
    if class_index >= len(baserec.BaseAnchor):
        return None

    anchor = baserec.BaseAnchor[class_index]
    if anchor is None:
        return None

    return (anchor.XCoordinate, anchor.YCoordinate)

def set_anchor_in_baserec(baserec, class_index, x, y):
    """
    Set BaseAnchor[class_index] in this BaseRecord to (x, y), creating Anchor if needed.
    """
    while len(baserec.BaseAnchor) <= class_index:
        baserec.BaseAnchor.append(None)

    anchor = baserec.BaseAnchor[class_index]
    if anchor is None:
        anchor = otTables.Anchor()
        anchor.Format = 1
        baserec.BaseAnchor[class_index] = anchor

    anchor.XCoordinate = x
    anchor.YCoordinate = y

# ------------------------------------------------------------
# Outline sampling
# ------------------------------------------------------------

GRID_STEP = 10    # units between sampled heights
STEM_TOL = 8      # units: an interval centre within this of the fit matches

class SegmentPen(BasePen):
    """Flattens an outline into line segments."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.segs = []

    def _moveTo(self, p):
        self.cur = self.start = p

    def _lineTo(self, p):
        self.segs.append((self.cur, p))
        self.cur = p

    def _curveToOne(self, a, b, c):
        p0 = self.cur
        for i in range(1, 17):
            u = i / 16
            q = tuple(
                (1 - u) ** 3 * p0[k] + 3 * (1 - u) ** 2 * u * a[k]
                + 3 * (1 - u) * u * u * b[k] + u ** 3 * c[k]
                for k in (0, 1)
            )
            self.segs.append((self.cur, q))
            self.cur = q

    def _closePath(self):
        if self.cur != self.start:
            self.segs.append((self.cur, self.start))

class PointPen(BasePen):
    """Samples points along an outline, straight edges included."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.pts = []

    def _moveTo(self, p):
        self.cur = self.start = p
        self.pts.append(p)

    def _lineTo(self, p):
        p0 = self.cur
        for i in range(1, 21):
            u = i / 20
            self.pts.append((p0[0] + (p[0] - p0[0]) * u, p0[1] + (p[1] - p0[1]) * u))
        self.cur = p

    def _curveToOne(self, a, b, c):
        p0 = self.cur
        for i in range(1, 25):
            u = i / 24
            self.pts.append(tuple(
                (1 - u) ** 3 * p0[k] + 3 * (1 - u) ** 2 * u * a[k]
                + 3 * (1 - u) * u * u * b[k] + u ** 3 * c[k]
                for k in (0, 1)
            ))
        self.cur = c

    def _closePath(self):
        self._lineTo(self.start)

def glyph_segments(glyphset, glyph_name):
    """The glyph's outline as line segments (SegmentPen)."""
    pen = SegmentPen(glyphset)
    glyphset[glyph_name].draw(pen)
    return pen.segs

def glyph_points(glyphset, glyph_name):
    """Points sampled along the glyph's outline (PointPen)."""
    pen = PointPen(glyphset)
    glyphset[glyph_name].draw(pen)
    return pen.pts

def intervals(segs, slope, y):
    """Ink intervals of the outline at height y, in sheared coordinates (x' = x - y tan)."""
    xs = sorted(
        x0 + (y - y0) * (x1 - x0) / (y1 - y0) - y * slope
        for (x0, y0), (x1, y1) in segs
        if (y0 - y) * (y1 - y) < 0
    )
    return list(zip(xs[0::2], xs[1::2]))

STEM_MIN_EDGE = 40    # units: the shortest straight edge, and the least overlap of the two, that can be a stem

def stem_edges(glyphset, glyph_name):
    """The glyph's straight edges (line segments, closing lines included) at least STEM_MIN_EDGE tall."""
    pen = RecordingPen()
    glyphset[glyph_name].draw(pen)
    edges, cur, start = [], None, None
    for op, args in pen.value:
        if op == "moveTo":
            cur = start = args[0]
            continue
        if op in ("closePath", "endPath"):
            seg, cur = (cur, start), None
        else:
            seg, cur = (cur, args[-1]), args[-1]
            if op != "lineTo":
                continue
        if seg[0] is not None and abs(seg[1][1] - seg[0][1]) >= STEM_MIN_EDGE:
            edges.append(seg)
    return edges

STEM_EDGE_TOL = 2     # units: an ink interval's end within this of a straight edge is that edge

def _line(seg):
    (x0, y0), (x1, y1) = seg
    return lambda y: x0 + (y - y0) * (x1 - x0) / (y1 - y0)

def _yrange(seg):
    return min(seg[0][1], seg[1][1]), max(seg[0][1], seg[1][1])

def stem_candidates(glyphset, glyph_name):
    """
    Every stem of the glyph with a straight edge, as (midline, y_bottom, y_top, kind).

    "pair": two straight edges that run in opposite directions and bound one
    ink interval (checked by a scanline at mid-height), overlapping by at
    least STEM_MIN_EDGE; the midline is the mean of the two edge lines, and
    the straight part is their overlap.
    "edge": a straight edge with no partner (the other side of the stem is a
    curve, as in the middle stem of semibold italic m); it takes the centres
    of the ink intervals that end at the edge, over the
    edge's height; the midline is the edge line moved by the median distance
    from the edge to those centres (so it keeps the edge's angle, which the
    curved side would skew), and the straight part is the edge's height.
    """
    segs = glyph_segments(glyphset, glyph_name)
    edges = stem_edges(glyphset, glyph_name)
    out, paired = [], set()

    def bounds_interval(xl, xr, y):
        return any(abs(a - xl) <= STEM_EDGE_TOL and abs(b - xr) <= STEM_EDGE_TOL for a, b in intervals(segs, 0, y))

    for i, e in enumerate(edges):
        for j in range(i + 1, len(edges)):
            f = edges[j]
            if (e[1][1] - e[0][1]) * (f[1][1] - f[0][1]) >= 0:
                continue  # same direction: not the two sides of a stem
            lo = max(_yrange(e)[0], _yrange(f)[0])
            hi = min(_yrange(e)[1], _yrange(f)[1])
            if hi - lo < STEM_MIN_EDGE:
                continue
            le, lf = _line(e), _line(f)
            y = (lo + hi) / 2 + 0.5
            xl, xr = sorted((le(y), lf(y)))
            if not bounds_interval(xl, xr, y):
                continue  # edges of two different stems
            out.append(((lambda y, le=le, lf=lf: (le(y) + lf(y)) / 2), lo, hi, "pair"))
            paired.update((i, j))
    for i, e in enumerate(edges):
        if i in paired:
            continue
        le, (lo, hi) = _line(e), _yrange(e)
        ys, ms = [], []
        for y in range(int(lo) + 1, int(hi)):
            x = le(y + 0.5)
            for a, b in intervals(segs, 0, y + 0.5):
                if abs(a - x) <= STEM_EDGE_TOL or abs(b - x) <= STEM_EDGE_TOL:
                    ys.append(y + 0.5); ms.append((a + b) / 2)
        if len(ys) < 5:
            continue
        shifts = sorted(m - le(y) for y, m in zip(ys, ms))
        d = shifts[len(shifts) // 2]
        out.append(((lambda y, le=le, d=d: le(y) + d), lo, hi, "edge"))
    return out

def stem_line(glyphset, glyph_name, central=False):
    """
    The straight part of the glyph's stem, from its control points (stem_candidates).

    By default the stem is the tallest candidate, a pair of edges before a
    single edge (i, j, l, combining i). With central=True it is the candidate
    whose midline, at mid-height of its straight part, is nearest the centre of
    the glyph's ink bounds with the slant of the stem removed (the middle stem
    of m). midline(y) is exact on the straight part and extends it linearly
    beyond, at the stem's own angle.
    Returns (midline, y_bottom, y_top), or None if the glyph has no stem.
    """
    cands = stem_candidates(glyphset, glyph_name)
    if not cands:
        return None
    if central:
        pen = BoundsPen(glyphset)
        glyphset[glyph_name].draw(pen)
        xmin, ymin, xmax, ymax = pen.bounds
        def dist(c):
            m, lo, hi, _ = c
            slope = (m(hi) - m(lo)) / (hi - lo)
            centre_at = lambda y: (xmin + xmax) / 2 + slope * (y - (ymin + ymax) / 2)
            return abs(m((lo + hi) / 2) - centre_at((lo + hi) / 2))
        best = min(cands, key=dist)
    else:
        best = max(cands, key=lambda c: (c[3] == "pair", c[2] - c[1]))
    return best[:3]

# ------------------------------------------------------------
# Fit of a base letter inside another letter
# ------------------------------------------------------------

def fit_intervals(sd, sb, slope, heights, max_dev):
    """
    Fit the base letter's ink intervals (segments sb) to the other letter's
    (segments sd) at the given heights (each sampled half a unit above, never
    exactly on a vertex). Return (scale, offset, match), or None if fewer
    than 3 intervals pair up.

    At each height, each interval of the base is paired with the other
    letter's interval of about the same width nearest to it. A line
    x_derived = scale * x_base + offset is fitted through the paired centres
    that lie within 40 of the median offset; scale is used only within
    max_dev of 1, else the fit is a shift. match is the share of all the
    base's intervals within STEM_TOL of the line.
    """
    pairs, total = [], 0
    for y in heights:
        y += 0.5
        ib, idv = intervals(sb, slope, y), intervals(sd, slope, y)
        total += len(ib)
        for a, b in ib:
            w, c = b - a, (a + b) / 2
            near = [(p + q) / 2 for p, q in idv if abs((q - p) - w) <= 0.2 * w + 4]
            if near:
                pairs.append((c, min(near, key=lambda z: abs(z - c))))
    if len(pairs) < 3 or not total:
        return None
    diffs = sorted(d - b for b, d in pairs)
    median = diffs[len(diffs) // 2]
    kept = [(b, d) for b, d in pairs if abs(d - b - median) <= 40]
    mb = sum(b for b, _ in kept) / len(kept)
    md = sum(d for _, d in kept) / len(kept)
    var = sum((b - mb) ** 2 for b, _ in kept)
    scale = sum((b - mb) * (d - md) for b, d in kept) / var if var > 1e-6 else 1.0
    if abs(scale - 1) > max_dev:
        scale = 1.0
    offset = md - scale * mb
    good = sum(1 for b, d in kept if abs(scale * b + offset - d) <= STEM_TOL)
    return scale, offset, good / total


MIN_FIT = 0.80            # share of the base's ink intervals on the inherited side that must fit
FIT_MAX_SCALE_DEV = 0.15  # a fitted scale further than this from 1 is not trusted: shift only
BANDS = {0: (150, 900), 2: (-400, 250)}  # heights compared: the inherited side only


def fit_base(ttfont, font_key, derived_glyph, base_glyph, anchor_class, base_xy):
    """
    Return (dx, match, scale): how far the base's anchor moves inside the
    derived or precomposed glyph, from fit_intervals on the inherited side
    only (BANDS), so that an added part, or a fused cedilla, ogonek or horn,
    on the other side does not count. dx is the fitted line's displacement
    at the mark's axis (the base anchor, slanted, with the style's K).
    """
    glyphset = ttfont.getGlyphSet()
    slope = SLOPE[font_key]
    k = SHIFT_K.get(font_key, {}).get(str(anchor_class), 0)
    axis = base_xy[0] - base_xy[1] * slope + k
    sd, sb = glyph_segments(glyphset, derived_glyph), glyph_segments(glyphset, base_glyph)
    lo, hi = BANDS[anchor_class]
    fit = fit_intervals(sd, sb, slope, range(lo, hi, GRID_STEP), FIT_MAX_SCALE_DEV)
    if fit is None:
        return 0, 0.0, 1.0
    scale, offset, match = fit
    return round(scale * axis + offset - axis), match, scale
