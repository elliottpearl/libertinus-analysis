# pen_stroke.py
"""
A broad-nib pen stroke: the outline swept by a flat nib (a rectangle W wide
and h deep, held at angle phi) moving along a centreline, fitted with cubic
Bézier curves. Used by missing_glyphs.py for ỿ's loop (2026-11-14).

The nib's width W, its hairline h and its angle phi describe a style's
stress: a stroke moving at angle a is |W sin(a - phi)| + |h cos(a - phi)|
thick, thick where the pen moves across its edge, thin where along it.

The sweep is the union of the convex hulls of consecutive nib positions
(boolean operations, but only to find the outline); the outline is then
refitted with few cubic curves (Schneider's algorithm), with on-curve
points at its corners and at its extremes in x and y, as a designer places
them.
"""

import math

import pathops


def thickness(direction, W, h, phi):
    """How thick a stroke moving at `direction` (radians) is with this nib."""
    a = direction - phi
    return abs(W * math.sin(a)) + abs(h * math.cos(a))


def _hull(points):
    pts = sorted(set(points))
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


def sweep(centreline, W, h, phi):
    """
    The outline swept by the nib along the centreline (a list of points):
    a pathops path (outer contour and counters).
    """
    c, s = math.cos(phi), math.sin(phi)
    half_w = (c * W / 2, s * W / 2)
    half_h = (-s * h / 2, c * h / 2)

    def nib(p):
        return [(p[0] + sx * half_w[0] + sy * half_h[0], p[1] + sx * half_w[1] + sy * half_h[1])
                for sx in (-1, 1) for sy in (-1, 1)]
    builder = pathops.OpBuilder(fix_winding=True, keep_starting_points=False)
    for a, b in zip(centreline, centreline[1:]):
        hull = _hull(nib(a) + nib(b))
        path = pathops.Path()
        path.moveTo(*hull[0])
        for q in hull[1:]:
            path.lineTo(*q)
        path.close()
        builder.add(path, pathops.PathOp.UNION)
    return builder.resolve()


# ------------------------------------------------------------
# Fitting a closed polyline with cubic curves (Schneider 1990)
# ------------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n) if n else (0.0, 0.0)


def _bez(b, t):
    u = 1 - t
    return tuple(u ** 3 * b[0][k] + 3 * u * u * t * b[1][k] + 3 * u * t * t * b[2][k] + t ** 3 * b[3][k]
                 for k in (0, 1))


def _bez_d(b, t, order):
    if order == 1:
        q = [tuple(3 * (b[i + 1][k] - b[i][k]) for k in (0, 1)) for i in range(3)]
        u = 1 - t
        return tuple(u * u * q[0][k] + 2 * u * t * q[1][k] + t * t * q[2][k] for k in (0, 1))
    q = [tuple(6 * (b[i + 2][k] - 2 * b[i + 1][k] + b[i][k]) for k in (0, 1)) for i in range(2)]
    return tuple((1 - t) * q[0][k] + t * q[1][k] for k in (0, 1))


def _generate(pts, us, t0, t3):
    """Least-squares handle lengths for fixed end tangents (t0 leaving pts[0], t3 leaving pts[-1] backward)."""
    p0, p3 = pts[0], pts[-1]
    c11 = c12 = c22 = x1 = x2 = 0.0
    for u, p in zip(us, pts):
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
        a1 = (t0[0] * b1, t0[1] * b1)
        a2 = (t3[0] * b2, t3[1] * b2)
        c11 += a1[0] ** 2 + a1[1] ** 2
        c12 += a1[0] * a2[0] + a1[1] * a2[1]
        c22 += a2[0] ** 2 + a2[1] ** 2
        r = (p[0] - (b0 + b1) * p0[0] - (b2 + b3) * p3[0], p[1] - (b0 + b1) * p0[1] - (b2 + b3) * p3[1])
        x1 += a1[0] * r[0] + a1[1] * r[1]
        x2 += a2[0] * r[0] + a2[1] * r[1]
    det = c11 * c22 - c12 * c12
    seg = math.dist(p0, p3)
    alpha = beta = seg / 3
    if abs(det) > 1e-12:
        alpha = (x1 * c22 - x2 * c12) / det
        beta = (c11 * x2 - c12 * x1) / det
    if alpha < seg * 1e-3 or beta < seg * 1e-3:
        alpha = beta = seg / 3
    return (p0, (p0[0] + t0[0] * alpha, p0[1] + t0[1] * alpha), (p3[0] + t3[0] * beta, p3[1] + t3[1] * beta), p3)


def _params(pts):
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.dist(a, b))
    return [x / d[-1] for x in d] if d[-1] else [0.0] * len(pts)


def _max_error(pts, bez, us):
    worst, split = 0.0, len(pts) // 2
    for i, (p, u) in enumerate(zip(pts, us)):
        e = math.dist(_bez(bez, u), p)
        if e > worst:
            worst, split = e, i
    return worst, split


def _reparam(pts, bez, us):
    out = []
    for p, u in zip(pts, us):
        q, q1, q2 = _bez(bez, u), _bez_d(bez, u, 1), _bez_d(bez, u, 2)
        num = (q[0] - p[0]) * q1[0] + (q[1] - p[1]) * q1[1]
        den = q1[0] ** 2 + q1[1] ** 2 + (q[0] - p[0]) * q2[0] + (q[1] - p[1]) * q2[1]
        out.append(min(1.0, max(0.0, u - num / den)) if den else u)
    return out


def fit_open(pts, tol, t0=None, t3=None):
    """Cubic segments fitting an open polyline within `tol` (Schneider's algorithm)."""
    if len(pts) < 2:
        return []
    t0 = t0 or _unit(_sub(pts[1], pts[0]))
    t3 = t3 or _unit(_sub(pts[-2], pts[-1]))
    if len(pts) == 2:
        d = math.dist(*pts) / 3
        return [(pts[0], (pts[0][0] + t0[0] * d, pts[0][1] + t0[1] * d),
                 (pts[1][0] + t3[0] * d, pts[1][1] + t3[1] * d), pts[1])]
    us = _params(pts)
    bez = _generate(pts, us, t0, t3)
    err, split = _max_error(pts, bez, us)
    if err < tol:
        return [bez]
    if err < tol * 4:
        for _ in range(20):
            us = _reparam(pts, bez, us)
            bez = _generate(pts, us, t0, t3)
            err, split = _max_error(pts, bez, us)
            if err < tol:
                return [bez]
    split = min(max(split, 1), len(pts) - 2)
    tc = _unit(_sub(pts[split - 1], pts[split + 1]))
    return fit_open(pts[:split + 1], tol, t0, tc) + fit_open(pts[split:], tol, (-tc[0], -tc[1]), t3)


def resample(pts, step):
    """A closed polyline resampled at equal steps."""
    ring = pts + [pts[0]]
    total = sum(math.dist(a, b) for a, b in zip(ring, ring[1:]))
    n = max(8, int(total / step))
    out, i, acc = [], 0, 0.0
    seglen = [math.dist(a, b) for a, b in zip(ring, ring[1:])]
    for k in range(n):
        target = k * total / n
        while i < len(seglen) - 1 and acc + seglen[i] < target:
            acc += seglen[i]
            i += 1
        t = (target - acc) / seglen[i] if seglen[i] else 0.0
        a, b = ring[i], ring[i + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def fit_closed(pts, tol=1.5, corner_deg=40.0, step=3.0):
    """
    A closed polyline as cubic segments: resampled, split at corners (a turn
    sharper than corner_deg over a few samples) and at the extremes in x and
    y, each piece fitted (Schneider). Returns a contour: [(p0, p1, p2, p3), ...].
    """
    pts = resample(pts, step)
    n = len(pts)
    k = 3
    turn = []
    for i in range(n):
        a = _unit(_sub(pts[i], pts[i - k]))
        b = _unit(_sub(pts[(i + k) % n], pts[i]))
        turn.append(math.degrees(math.acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1])))))
    splits = set()
    # Corners: local maxima of the turn above the threshold.
    for i in range(n):
        if turn[i] > corner_deg and turn[i] >= turn[i - 1] and turn[i] >= turn[(i + 1) % n]:
            splits.add(i)
    # Extremes in x and y (local, over a window), away from corners.
    w = 6
    for i in range(n):
        for axis in (0, 1):
            vals = [pts[(i + j) % n][axis] for j in range(-w, w + 1)]
            v = pts[i][axis]
            if (v == max(vals) or v == min(vals)) and max(vals) - min(vals) > 1.0:
                if all(min(abs(i - s), n - abs(i - s)) > w for s in splits):
                    splits.add(i)
    splits = sorted(splits)
    if not splits:
        splits = [0, n // 2]
    contour = []
    for a, b in zip(splits, splits[1:] + [splits[0] + n]):
        piece = [pts[j % n] for j in range(a, b + 1)]
        corner_a, corner_b = turn[a % n] > corner_deg, turn[b % n] > corner_deg
        t0 = None if corner_a else _unit(_sub(pts[(a + 1) % n], pts[(a - 1) % n]))
        t3 = None if corner_b else _unit(_sub(pts[(b - 1) % n], pts[(b + 1) % n]))
        contour += fit_open(piece, tol, t0, t3)
    # Exact closure: each segment starts where the previous one ends.
    for i in range(len(contour)):
        prev = contour[i - 1]
        contour[i] = (prev[-1],) + tuple(contour[i][1:])
    return [tuple(seg) for seg in contour]
