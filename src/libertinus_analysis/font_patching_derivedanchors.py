# font_patching_derivedanchors.py
"""
Derived-letter stage of the Libertinus patching pipeline (stage 8).

A derived letter is a base letter plus a bar, stroke, hook, tail, curl or belt
(data/derived_letters.py). Where the added part stays clear of a mark, the
derived letter takes the base letter's final anchor (after the curated
anchors of stage 7), moved by the horizontal shift between the two outlines:
the designer often drew the derived letter in a shifted frame (Ɗ is D moved
about 80 units right), and a hook skews the bounding box that the heuristic
candidate is centred on.

The anchor's Y is the base letter's, unless the derived letter's added part
reaches further into the mark's zone than the base letter does: then Y moves
away by the difference, so the mark keeps the base letter's clearance. The
zone is MARK_HALF_WIDTH either side of the mark's axis (slanted in italic,
with the style's K): above, the highest point of the outline there; below,
the lowest. Where the derived letter is shorter there, Y stays, so marks keep
the height they have on the base letter.

The shift is found by matching outlines: at every height on a 10-unit grid,
the x positions where the base's outline crosses that height are compared
with the derived letter's, and the shift that pairs most crossings (within
MATCH_TOL) wins. The fraction of the base's crossings so paired measures how
much of the base letter the derived letter really contains; below MIN_MATCH
the derived letter was redrawn, and nothing is inherited in that style.

Behavior:
    - Overwrites designer and heuristic anchors of the listed classes.
    - Never overwrites a curated anchor of the derived letter (stage 7).
    - Skips a class the base letter has no anchor for.
"""

from collections import Counter

from fontTools.pens.basePen import BasePen

from .font_patching_anchors import load_human_anchors
from .fontmetrics_helpers import SHIFT_K, SLOPE
from .font_patching_precomposed_anchors import (
    ensure_base_record_for_glyph,
    find_mark_to_base_subtables,
    get_anchor_from_baserec,
    get_base_record_for_glyph,
    set_anchor_in_baserec,
)

MIN_MATCH = 0.70  # share of the base's outline found in the derived letter
MATCH_TOL = 6     # units: a crossing within this of the shifted base matches
GRID_STEP = 10    # units between sampled heights
MARK_HALF_WIDTH = 120  # units either side of the mark's axis: a wide mark
MIN_DY = 6        # smaller differences in reach are left alone

CLASS_NAMES = {0: "above", 2: "below"}

# ------------------------------------------------------------
# Data
# ------------------------------------------------------------

def load_derived_letters():
    """Return (derived, derived_by_name) from data/derived_letters.py."""
    mod = __import__("data.derived_letters", fromlist=["derived", "derived_by_name"])
    return mod.derived, mod.derived_by_name

def style_classes(classes, font_key):
    """The anchor classes of a dict entry for this style (tuple or per-style dict)."""
    if isinstance(classes, dict):
        return tuple(classes.get(font_key, ()))
    return tuple(classes)

def derived_pairs(cmap, font_key):
    """
    All (derived glyph, base glyph, classes, label) in this font, from both
    dicts. label names the derived letter for reports.
    """
    derived, derived_by_name = load_derived_letters()
    pairs = []
    for cp, (base_cp, classes) in derived.items():
        if cp in cmap and base_cp in cmap:
            pairs.append((cmap[cp], cmap[base_cp], style_classes(classes, font_key), f"U+{cp:04X}"))
    for name, (base_name, classes) in derived_by_name.items():
        pairs.append((name, base_name, style_classes(classes, font_key), name))
    return pairs

# ------------------------------------------------------------
# Outline matching
# ------------------------------------------------------------

class _SegmentPen(BasePen):
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

def _crossings(glyphset, glyph_name):
    """{height: sorted x of the outline crossing it}, on a fixed grid."""
    pen = _SegmentPen(glyphset)
    glyphset[glyph_name].draw(pen)
    ys = [y for seg in pen.segs for _, y in seg]
    if not ys:
        return {}
    lo, hi = min(ys), max(ys)
    out = {}
    for y in range(-400, 1100, GRID_STEP):
        y += 0.5  # never exactly on a vertex
        if lo < y < hi:
            out[y] = sorted(
                x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                for (x0, y0), (x1, y1) in pen.segs
                if (y0 - y) * (y1 - y) < 0
            )
    return out

def outline_shift(ttfont, derived_glyph, base_glyph):
    """
    Return (dx, match): the horizontal shift of the base letter inside the
    derived letter, and the share of the base's outline it accounts for.
    """
    glyphset = ttfont.getGlyphSet()
    cd = _crossings(glyphset, derived_glyph)
    cb = _crossings(glyphset, base_glyph)

    votes = Counter()
    for y, xs in cb.items():
        for xb in xs:
            for xd in cd.get(y, []):
                votes[round((xd - xb) / 2) * 2] += 1
    if not votes:
        return 0, 0.0

    def score(dx):
        return sum(votes.get(dx + e, 0) for e in range(-MATCH_TOL, MATCH_TOL + 1, 2))

    dx = max(votes, key=score)
    total = sum(len(xs) for xs in cb.values())
    hits = sum(
        1 for y, xs in cb.items() for xb in xs
        if any(abs(xd - xb - dx) <= MATCH_TOL for xd in cd.get(y, []))
    )
    return dx, hits / total

class _PointPen(BasePen):
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

def _reach(ttfont, glyph_name, axis, slope, cls, offset=0):
    """
    Highest (above) or lowest (below) point of the outline within
    MARK_HALF_WIDTH of the mark's axis (sheared coordinates), with the
    outline moved right by offset. None if no ink there.
    """
    glyphset = ttfont.getGlyphSet()
    pen = _PointPen(glyphset)
    glyphset[glyph_name].draw(pen)
    ys = [y for x, y in pen.pts if abs(x + offset - y * slope - axis) <= MARK_HALF_WIDTH]
    if not ys:
        return None
    return max(ys) if cls == 0 else min(ys)

def inherited_anchor(ttfont, font_key, derived_glyph, base_glyph, base_xy, cls, dx):
    """
    The derived letter's anchor: the base letter's anchor moved right by dx,
    and moved away in Y where the derived letter reaches further into the
    mark's zone. Returns (x, y, dy).
    """
    slope = SLOPE[font_key]
    k = SHIFT_K.get(font_key, {}).get(str(cls), 0)
    x, y = base_xy[0] + dx, base_xy[1]
    axis = x - y * slope + k  # the mark's axis, in sheared coordinates
    rd = _reach(ttfont, derived_glyph, axis, slope, cls)
    rb = _reach(ttfont, base_glyph, axis, slope, cls, offset=dx)
    dy = 0
    if rd is not None and rb is not None:
        diff = rd - rb
        if (cls == 0 and diff >= MIN_DY) or (cls == 2 and diff <= -MIN_DY):
            dy = round(diff)
    # x follows the slant when y moves: the mark stays on the same axis
    return round(x + dy * slope), y + dy, dy

# ------------------------------------------------------------
# Curated anchors of a derived glyph
# ------------------------------------------------------------

def curated_classes(font_key, glyph_name, cmap_reverse):
    """Anchor classes curated for this glyph in data/fontanchors_human/."""
    human = load_human_anchors(font_key)
    classes = set(human.get("bases_by_name", {}).get(glyph_name, {}))
    cp = cmap_reverse.get(glyph_name)
    if cp is not None:
        classes |= set(human.get("bases", {}).get(cp, {}))
    return classes

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def patch_derived_anchors(ttfont, font_key, lookup_index):
    """
    Give each derived letter its base letter's anchor plus the outline shift,
    for the listed classes. Returns: list of report lines.
    """
    subtables = find_mark_to_base_subtables(ttfont, lookup_index)
    if not subtables:
        return [f"No MarkToBase (LookupType 4) subtables found in lookup {lookup_index}; SKIPPED"]
    sub = subtables[0]

    cmap = ttfont.getBestCmap()
    cmap_reverse = {g: u for u, g in cmap.items()}
    glyph_order = set(ttfont.getGlyphOrder())

    report = []
    inherited = 0
    for derived_glyph, base_glyph, classes, label in derived_pairs(cmap, font_key):
        if not classes:
            continue
        if derived_glyph not in glyph_order or base_glyph not in glyph_order:
            report.append(f"{label} {derived_glyph}: glyph missing; SKIPPED")
            continue

        dx, match = outline_shift(ttfont, derived_glyph, base_glyph)
        if match < MIN_MATCH:
            report.append(
                f"{label} {derived_glyph} < {base_glyph}: outline match {match:.0%} "
                f"(shift {dx:+d}) below {MIN_MATCH:.0%}; SKIPPED"
            )
            continue

        curated = curated_classes(font_key, derived_glyph, cmap_reverse)
        base_rec, _ = get_base_record_for_glyph(sub, base_glyph)
        for cls in classes:
            name = CLASS_NAMES[cls]
            if cls in curated:
                report.append(f"{label} {derived_glyph}: {name} anchor is curated; kept")
                continue
            base_xy = get_anchor_from_baserec(base_rec, cls) if base_rec else None
            if base_xy is None:
                report.append(f"{label} {derived_glyph}: base {base_glyph} has no {name} anchor; SKIPPED")
                continue

            rec, _ = ensure_base_record_for_glyph(sub, derived_glyph)
            old = get_anchor_from_baserec(rec, cls)
            x, y, dy = inherited_anchor(ttfont, font_key, derived_glyph, base_glyph, base_xy, cls, dx)
            set_anchor_in_baserec(rec, cls, x, y)
            inherited += 1
            moved = f", y moved {dy:+d} to clear the added part" if dy else ""
            report.append(
                f"{label} {derived_glyph}: {name} anchor ({x}, {y}) from {base_glyph} "
                f"{base_xy} shift {dx:+d} (match {match:.0%}){moved}; was {old}"
            )

    report.append(f"derived-letter anchors inherited: {inherited}")
    return report
