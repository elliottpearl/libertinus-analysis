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
the lowest. Only ink beyond the base letter's own highest (lowest) point
counts, since the base anchor's Y already clears that. Where the derived
letter is shorter there, Y stays, so marks keep the height they have on the
base letter.

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
from .fontmetrics_helpers import SHIFT_K, SLOPE, get_anchor_candidate
from .fontmetrics_loader import load_fontmetrics
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

# Letters matched on stems (stem_match in data/derived_letters.py): bottom tails, and ɗ
STEM_LO = 60      # stem fit: heights from here to the letter's top (at most XHEIGHT) minus this
XHEIGHT = 645
STEM_TOL = 8      # units: a stem centre within this of the fit matches
MAX_SCALE_DEV = 0.10  # a fitted scale further than this from 1 is not trusted: shift only
WIDE_SCALE_DEV = 0.15  # second try where the stems match too little: a letter drawn wider on one side
                       # (italic ɲ: n's left stem, the right leg 32 further right; scale 1.12)
TAIL_Y = -30      # ink below this is the tail
BELOW_ZONE = 195  # either side of the mark's axis: the widest below mark (U+0347)

CLASS_NAMES = {0: "above", 2: "below"}

# ------------------------------------------------------------
# Data
# ------------------------------------------------------------

def load_derived_letters():
    """Return (derived, derived_by_name) from data/derived_letters.py."""
    mod = __import__("data.derived_letters", fromlist=["derived", "derived_by_name"])
    return mod.derived, mod.derived_by_name

def load_derived_y():
    """Return derived_y from data/derived_letters.py."""
    return __import__("data.derived_letters", fromlist=["derived_y"]).derived_y

def load_stem_match():
    """Return stem_match from data/derived_letters.py: letters matched on their stems."""
    return __import__("data.derived_letters", fromlist=["stem_match"]).stem_match

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

    total = sum(len(xs) for xs in cb.values())

    def hits(d):
        return sum(
            1 for y, xs in cb.items() for xb in xs
            if any(abs(xd - xb - d) <= MATCH_TOL for xd in cd.get(y, []))
        )

    dx = max(votes, key=score)
    # within the winning window, the peak of the votes among the shifts that
    # pair nearly the most crossings (98%): the window alone can win at its
    # edge, where crossings that coincide exactly then miss (italic Ł, ł: +6 and
    # 56%, 42%, instead of 0 and 95%), and an added part's own crossings can
    # pair a few more a little off the copy (ł +4) (2026-11-10)
    window = {d: hits(d) for d in range(dx - MATCH_TOL, dx + MATCH_TOL + 1, 2)}
    best = max(window.values())
    dx = max((d for d, h in window.items() if h >= 0.98 * best),
             key=lambda d: (votes.get(d, 0), window[d], -abs(d - dx)))
    return dx, hits(dx) / total

def _segments(glyphset, glyph_name):
    pen = _SegmentPen(glyphset)
    glyphset[glyph_name].draw(pen)
    return pen.segs

def _intervals(segs, slope, y):
    """Ink intervals of the outline at height y, in sheared coordinates (x' = x - y tan)."""
    xs = sorted(
        x0 + (y - y0) * (x1 - x0) / (y1 - y0) - y * slope
        for (x0, y0), (x1, y1) in segs
        if (y0 - y) * (y1 - y) < 0
    )
    return list(zip(xs[0::2], xs[1::2]))

def stem_shift(ttfont, font_key, derived_glyph, base_glyph, axis, max_dev=MAX_SCALE_DEV):
    """
    Return (dx, match) for a bottom-tail letter: the horizontal shift of the
    base letter inside the derived letter at the mark's axis, matched on the
    stems and bowl sides above the tail.

    At every height from STEM_LO to the top (at most the x-height) minus
    STEM_LO, each ink interval of the base is paired with the derived
    letter's interval of about the same width nearest to it. A line
    x_derived = a * x_base + b through the paired centres allows for a letter
    drawn slightly narrower or wider (a is used only within MAX_SCALE_DEV of
    1; max_dev), and dx is its shift at the axis. match is the share of the base's
    intervals within STEM_TOL of the line.
    """
    glyphset = ttfont.getGlyphSet()
    slope = SLOPE[font_key]
    sd, sb = _segments(glyphset, derived_glyph), _segments(glyphset, base_glyph)
    top = min(max(y for seg in s for _, y in seg) for s in (sd, sb))
    pairs, total = [], 0
    for y in range(STEM_LO, int(min(top, XHEIGHT)) - STEM_LO, GRID_STEP):
        y += 0.5
        ib, idv = _intervals(sb, slope, y), _intervals(sd, slope, y)
        total += len(ib)
        for a, b in ib:
            w, c = b - a, (a + b) / 2
            near = [(p + q) / 2 for p, q in idv if abs((q - p) - w) <= 0.2 * w + 4]
            if near:
                pairs.append((c, min(near, key=lambda z: abs(z - c))))
    if len(pairs) < 3 or not total:
        return 0, 0.0
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
    return round(scale * axis + offset - axis), good / total

def _tail_reaches(ttfont, font_key, glyph_name, axis):
    """True if the outline has ink below TAIL_Y within BELOW_ZONE of the mark's axis (sheared)."""
    glyphset = ttfont.getGlyphSet()
    pen = _PointPen(glyphset)
    glyphset[glyph_name].draw(pen)
    slope = SLOPE[font_key]
    return any(y < TAIL_Y and abs(x - y * slope - axis) <= BELOW_ZONE for x, y in pen.pts)

def tail_anchor(ttfont, font_key, cp, derived_glyph, base_glyph, base_xy, cls):
    """
    The anchor of a bottom-tail letter in class cls, or None to leave it.
    Returns (x, y, note).

    X is the base letter's X plus the stem shift. Above, Y is the base
    letter's (moved away where the derived letter reaches higher, as for the
    other derived letters). Below, where the tail has ink within BELOW_ZONE of
    the mark's axis, Y is the anchor-model candidate (the descender reference
    and its clearance, from the letter's own outline) and X follows the slant
    to it; elsewhere, Y is the base letter's. Where the stems match too
    little, nothing is inherited; below, a tail that reaches the mark still
    gets the candidate, X and Y.
    """
    slope = SLOPE[font_key]
    k = SHIFT_K.get(font_key, {}).get(str(cls), 0)
    axis = base_xy[0] - base_xy[1] * slope + k
    dx, match = stem_shift(ttfont, font_key, derived_glyph, base_glyph, axis)
    if match < MIN_MATCH:
        # Only where the first fit fails, so that letters already matched keep their shift
        wide = stem_shift(ttfont, font_key, derived_glyph, base_glyph, axis, WIDE_SCALE_DEV)
        if wide[1] >= MIN_MATCH:
            dx, match = wide
    ok = match >= MIN_MATCH
    if cls == 0:
        if not ok:
            return None, f"stem match {match:.0%} (shift {dx:+d}) below {MIN_MATCH:.0%}"
        x, y, dy = inherited_anchor(ttfont, font_key, derived_glyph, base_glyph, base_xy, cls, dx)
        moved = f", y moved {dy:+d} to clear the added part" if dy else ""
        return (x, y), f"shift {dx:+d} (stem match {match:.0%}){moved}"

    reaches = _tail_reaches(ttfont, font_key, derived_glyph, axis + dx)
    if reaches:
        cand = get_anchor_candidate(font_key, load_fontmetrics(font_key), cp, str(cls))
        y = round(cand[1])
        if not ok:
            return ((round(cand[0]), y),
                    f"stem match {match:.0%} below {MIN_MATCH:.0%}; tail under the mark: candidate")
        x = round(base_xy[0] + dx + (y - base_xy[1]) * slope)
        return (x, y), f"shift {dx:+d} (stem match {match:.0%}); tail under the mark: candidate y"
    if not ok:
        return None, f"stem match {match:.0%} (shift {dx:+d}) below {MIN_MATCH:.0%}"
    return (base_xy[0] + dx, base_xy[1]), f"shift {dx:+d} (stem match {match:.0%}); tail clear of the mark"

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

def _points(ttfont, glyph_name):
    glyphset = ttfont.getGlyphSet()
    pen = _PointPen(glyphset)
    glyphset[glyph_name].draw(pen)
    return pen.pts

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
        # The base anchor's Y clears the base letter's highest (lowest) point, so
        # only ink beyond that can reach the mark. Without this, a narrower
        # redrawing of a diagonal near the zone's edge (semibold italic Ɲ against
        # N) counts as a higher reach although it stays below the base's top.
        ys = [p[1] for p in _points(ttfont, base_glyph)]
        rb = max(rb, max(ys)) if cls == 0 else min(rb, min(ys))
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

def _patch_tail_letter(ttfont, font_key, sub, cp, derived_glyph, base_glyph, classes, label,
                       cmap_reverse, report):
    """Stage 8 for a letter in stem_match (tail_anchor). Returns the number of anchors set."""
    curated = curated_classes(font_key, derived_glyph, cmap_reverse)
    base_rec, _ = get_base_record_for_glyph(sub, base_glyph)
    count = 0
    for cls in classes:
        name = CLASS_NAMES[cls]
        if cls in curated:
            report.append(f"{label} {derived_glyph}: {name} anchor is curated; kept")
            continue
        base_xy = get_anchor_from_baserec(base_rec, cls) if base_rec else None
        if base_xy is None:
            report.append(f"{label} {derived_glyph}: base {base_glyph} has no {name} anchor; SKIPPED")
            continue
        xy, note = tail_anchor(ttfont, font_key, cp, derived_glyph, base_glyph, base_xy, cls)
        if xy is None:
            report.append(f"{label} {derived_glyph} < {base_glyph}: {name}: {note}; SKIPPED")
            continue
        rec, _ = ensure_base_record_for_glyph(sub, derived_glyph)
        old = get_anchor_from_baserec(rec, cls)
        set_anchor_in_baserec(rec, cls, xy[0], xy[1])
        count += 1
        report.append(f"{label} {derived_glyph}: {name} anchor ({xy[0]}, {xy[1]}) from {base_glyph} "
                      f"{base_xy}, {note}; was {old}")
    return count

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
    stem_match = load_stem_match()
    for derived_glyph, base_glyph, classes, label in derived_pairs(cmap, font_key):
        if not classes:
            continue
        if derived_glyph not in glyph_order or base_glyph not in glyph_order:
            report.append(f"{label} {derived_glyph}: glyph missing; SKIPPED")
            continue

        cp = cmap_reverse.get(derived_glyph)
        if cp in stem_match:
            inherited += _patch_tail_letter(ttfont, font_key, sub, cp, derived_glyph, base_glyph,
                                            classes, label, cmap_reverse, report)
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

    for cp, (base_cp, by_class) in load_derived_y().items():
        derived_glyph, base_glyph = cmap[cp], cmap[base_cp]
        curated = curated_classes(font_key, derived_glyph, cmap_reverse)
        base_rec, _ = get_base_record_for_glyph(sub, base_glyph)
        dx, _ = outline_shift(ttfont, derived_glyph, base_glyph)
        for cls, ys in by_class.items():
            name = CLASS_NAMES[cls]
            if cls in curated:
                report.append(f"U+{cp:04X} {derived_glyph}: {name} anchor is curated; kept")
                continue
            base_x, base_y = get_anchor_from_baserec(base_rec, cls)
            y = ys[font_key]
            x = round(base_x + dx + (y - base_y) * SLOPE[font_key])

            rec, _ = ensure_base_record_for_glyph(sub, derived_glyph)
            old = get_anchor_from_baserec(rec, cls)
            set_anchor_in_baserec(rec, cls, x, y)
            inherited += 1
            report.append(
                f"U+{cp:04X} {derived_glyph}: {name} anchor ({x}, {y}), x from {base_glyph} "
                f"({base_x}, {base_y}) shift {dx:+d}; was {old}"
            )

    report.append(f"derived-letter anchors inherited: {inherited}")
    return report
