# glyph_construction.py
"""
Glyph outlines built from components, the way a font source builds them:
whole contours of existing glyphs (references, under an affine transform),
simple part contours (a bar, a stroke), and splices of two contours at their
crossings with a line. No boolean operations: the result keeps every
component's own points, overlapping where the components overlap (CFF fills
overlaps; font generation merges them). Splicing adds points only where a
contour is cut, and drops those that end up in the middle of a straight line.

Used by missing_glyphs.py (the drafts of the letters the non-regular styles
lack, 2026-11-13).

A contour is a list of segments; a segment is a tuple of points, two for a
line, four for a cubic curve, the first point being the end of the previous
segment. Contours are closed.
"""

import math

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

# ------------------------------------------------------------
# Reading and writing
# ------------------------------------------------------------

def contours_of(glyphset, name, matrix=(1, 0, 0, 1, 0, 0)):
    """The glyph's contours (components decomposed), transformed."""
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(TransformPen(pen, matrix))
    return _from_recording(pen.value)


def _from_recording(recording):
    contours, segs, start, cur = [], [], None, None
    for op, pts in recording:
        if op == "moveTo":
            start = cur = pts[0]
            segs = []
        elif op == "lineTo":
            segs.append((cur, pts[0]))
            cur = pts[0]
        elif op == "curveTo":
            segs.append((cur, *pts))
            cur = pts[-1]
        elif op == "qCurveTo":
            raise ValueError("quadratic outlines are not supported")
        elif op in ("closePath", "endPath"):
            if cur != start and math.dist(cur, start) > 1e-6:
                segs.append((cur, start))
            if segs:
                contours.append(segs)
            segs = []
    return contours


def draw(contours, pen):
    """Draw contours with a segment pen."""
    for segs in contours:
        pen.moveTo(segs[0][0])
        for seg in segs:
            if len(seg) == 2:
                pen.lineTo(seg[1])
            else:
                pen.curveTo(*seg[1:])
        pen.closePath()


def transform(contours, matrix):
    xx, xy, yx, yy, dx, dy = matrix

    def t(p):
        return (xx * p[0] + yx * p[1] + dx, xy * p[0] + yy * p[1] + dy)
    return [[tuple(t(p) for p in seg) for seg in segs] for segs in contours]


def bounds(contours):
    pts = [p for segs in contours for seg in segs for p in seg]
    return (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))


def on_curve_count(contours):
    return sum(len(segs) for segs in contours)


def signed_area(segs, steps=16):
    pts = [_point(seg, i / steps) for seg in segs for i in range(steps)]
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2


# ------------------------------------------------------------
# Segments
# ------------------------------------------------------------

def _point(seg, t):
    if len(seg) == 2:
        (x0, y0), (x1, y1) = seg
        return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
    a, b, c, d = seg
    u = 1 - t
    return tuple(u ** 3 * a[k] + 3 * u * u * t * b[k] + 3 * u * t * t * c[k] + t ** 3 * d[k] for k in (0, 1))


def split(seg, t):
    """Split a segment at parameter t (exactly, de Casteljau): two segments."""
    if len(seg) == 2:
        m = _point(seg, t)
        return (seg[0], m), (m, seg[1])
    a, b, c, d = seg

    def lerp(p, q):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    ab, bc, cd = lerp(a, b), lerp(b, c), lerp(c, d)
    abc, bcd = lerp(ab, bc), lerp(bc, cd)
    m = lerp(abc, bcd)
    return (a, ab, abc, m), (m, bcd, cd, d)


# ------------------------------------------------------------
# Crossings with a line
# ------------------------------------------------------------

def crossings(segs, line):
    """
    Where a contour crosses a line. `line` is (x0, y0, x1, y1), two points on
    it. Returns [(segment index, t, point)] in contour order.
    """
    lx0, ly0, lx1, ly1 = line

    def side(p):
        return (lx1 - lx0) * (p[1] - ly0) - (ly1 - ly0) * (p[0] - lx0)
    out = []
    for i, seg in enumerate(segs):
        n = 1 if len(seg) == 2 else 64
        prev_t, prev_s = 0.0, side(seg[0])
        for k in range(1, n + 1):
            t = k / n
            s = side(_point(seg, t))
            if (prev_s < 0) != (s < 0):
                lo, hi = prev_t, t
                for _ in range(60):
                    mid = (lo + hi) / 2
                    if (side(_point(seg, mid)) < 0) == (prev_s < 0):
                        lo = mid
                    else:
                        hi = mid
                tt = (lo + hi) / 2
                out.append((i, tt, _point(seg, tt)))
            prev_t, prev_s = t, s
    return out


def horizontal(y):
    """A horizontal line at y, running to the right."""
    return (0.0, y, 1.0, y)


def slanted(x_at_0, slope):
    """A line x = x_at_0 + y * slope, running upward."""
    return (x_at_0, 0.0, x_at_0 + slope * 1000, 1000.0)


# ------------------------------------------------------------
# Cutting a contour into a path between two crossings
# ------------------------------------------------------------

def path_between(segs, c_from, c_to):
    """
    The open path along the contour from crossing c_from to crossing c_to
    (forward, wrapping round), splitting the two segments at the crossings.
    Crossings are (segment index, t, ...).
    """
    i0, t0 = c_from[0], c_from[1]
    i1, t1 = c_to[0], c_to[1]
    n = len(segs)
    out = []
    first = segs[i0]
    if i0 == i1 and t1 > t0:
        # Both on one segment.
        _, rest = split(first, t0) if t0 > 0 else (None, first)
        t = (t1 - t0) / (1 - t0) if t0 < 1 else 0
        piece, _ = split(rest, t)
        return [piece]
    head = split(first, t0)[1] if t0 > 0 else first
    if t0 < 1 - 1e-9:
        out.append(head)
    i = (i0 + 1) % n
    while i != i1:
        out.append(segs[i])
        i = (i + 1) % n
    if t1 > 1e-9:
        out.append(split(segs[i1], t1)[0] if t1 < 1 else segs[i1])
    return out


def join(*paths):
    """
    One closed contour from open paths in order: the end of each path is
    joined to the start of the next by a line (none if they meet).
    """
    segs = []
    for k, path in enumerate(paths):
        if segs and math.dist(segs[-1][-1], path[0][0]) > 0.01:
            segs.append((segs[-1][-1], path[0][0]))
        elif segs:
            path = [(segs[-1][-1],) + tuple(path[0][1:])] + path[1:]
        segs.extend(path)
    if math.dist(segs[-1][-1], segs[0][0]) > 0.01:
        segs.append((segs[-1][-1], segs[0][0]))
    else:
        segs[-1] = tuple(segs[-1][:-1]) + (segs[0][0],)
    return segs


# ------------------------------------------------------------
# Clean-up
# ------------------------------------------------------------

def merge_lines(segs, tol=1.0, near=None):
    """
    Drop on-curve points between two lines that lie within `tol` of the line
    joining their neighbours (and, if `near` is a function of a point, only
    where it is true), and zero-length segments.
    """
    segs = list(segs)
    changed = True
    while changed and len(segs) > 2:
        changed = False
        n = len(segs)
        for i in range(n):
            a, b = segs[i], segs[(i + 1) % n]
            if math.dist(a[0], a[-1]) < 0.01 and len(a) == 2:
                segs = segs[:i] + segs[i + 1:]
                changed = True
                break
            if len(a) == 2 and len(b) == 2 and (near is None or near(a[1])):
                p, q, r = a[0], a[1], b[1]
                dx, dy = r[0] - p[0], r[1] - p[1]
                L = math.hypot(dx, dy)
                if L > 0 and abs(dy * (q[0] - p[0]) - dx * (q[1] - p[1])) / L < tol:
                    merged = (p, r)
                    if i + 1 < n:
                        segs = segs[:i] + [merged] + segs[i + 2:]
                    else:
                        segs = [merged] + segs[1:-1]
                    changed = True
                    break
    return segs


def straighten(segs, tol=2.0):
    """Curves whose control points lie within `tol` of their chord become lines."""
    out = []
    for seg in segs:
        if len(seg) == 4:
            p, a, b, q = seg
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy)
            if L > 0 and all(abs(dy * (c[0] - p[0]) - dx * (c[1] - p[1])) / L < tol for c in (a, b)):
                seg = (p, q)
        out.append(seg)
    return out


# ------------------------------------------------------------
# Splicing
# ------------------------------------------------------------

def _pick(cross, target):
    """The crossing nearest the target: an x, or a point (x, y)."""
    if isinstance(target, tuple):
        return min(cross, key=lambda c: math.dist(c[2], target))
    return min(cross, key=lambda c: abs(c[2][0] - target))


def splice(base, donor, line, base_xs, donor_xs, keep_base_left=True, donor_line=None):
    """
    Join the base contour on one side of a line to the donor contour on the
    other side.

    line: the joining line, two points (x0, y0, x1, y1); "left" is the left
    of its direction (above, for a horizontal line running right).
    base_xs, donor_xs: two targets (an x, or a point) near which each
    contour's two crossings are (a stem's two edges, say). keep_base_left: keep the base left of the line
    and the donor right of it, or the other way round. donor_line: the
    donor's own cutting line, if not the same.
    Returns the spliced contour; where the cut points do not meet, a line
    joins them.
    """
    donor_line = donor_line or line
    want = 1 if keep_base_left else -1
    cb, cd = crossings(base, line), crossings(donor, donor_line)
    b0, b1 = _pick(cb, base_xs[0]), _pick(cb, base_xs[1])
    d0, d1 = _pick(cd, donor_xs[0]), _pick(cd, donor_xs[1])
    # The base keeps the path that is not wholly on the removed side (the
    # removed part, a stem's end, is; what is kept may cross the line again,
    # as u's right stem does); the donor keeps the path wholly on its side.
    p01, p10 = path_between(base, b0, b1), path_between(base, b1, b0)
    if wholly(p01, line, -want):
        base_path, b_end = p10, b0
    elif wholly(p10, line, -want):
        base_path, b_end = p01, b1
    elif signed_side(p01, line) == want:
        base_path, b_end = p01, b1
    else:
        base_path, b_end = p10, b0
    # The donor path starts at the crossing on the same edge as the base path's end.
    d_start, d_stop = (d0, d1) if b_end is b0 else (d1, d0)
    donor_path = path_between(donor, d_start, d_stop)
    if not wholly(donor_path, donor_line, -want) and (
            wholly(path_between(donor, d_stop, d_start), donor_line, -want)
            or signed_side(donor_path, donor_line) == want):
        # The donor runs the other way round: take its other side, reversed.
        donor_path = reverse_path(path_between(donor, d_stop, d_start))
    return join(base_path, donor_path)


def wholly(path, line, sign, tol=0.5):
    """Whether the path lies wholly on one side of the line (sign +1 left, -1 right)."""
    lx0, ly0, lx1, ly1 = line
    L = math.hypot(lx1 - lx0, ly1 - ly0)
    for seg in path:
        for k in range(9):
            q = _point(seg, k / 8)
            d = ((lx1 - lx0) * (q[1] - ly0) - (ly1 - ly0) * (q[0] - lx0)) / L
            if d * sign < -tol:
                return False
    return True


def signed_side(path, line):
    lx0, ly0, lx1, ly1 = line
    s = 0.0
    for seg in path:
        p = _point(seg, 0.5)
        s += (lx1 - lx0) * (p[1] - ly0) - (ly1 - ly0) * (p[0] - lx0)
    return 1 if s >= 0 else -1


def reverse_path(path):
    return [tuple(reversed(seg)) for seg in reversed(path)]


def reverse(segs):
    """A contour's direction reversed."""
    return reverse_path(segs)
