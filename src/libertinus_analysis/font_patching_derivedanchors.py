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

The shift is found by fitting the base letter's ink to the derived letter's
(fit_base in font_patching_inherit, shared with stage 9, 2026-11-11): on the inherited side only, ink
intervals of the base are paired with intervals of about the same width, and
a line x_derived = scale * x_base + offset through the paired centres allows
for a letter drawn up to 15% wider or narrower (the italic capitals with a
hook or bar are about 4% wider than their bases). The shift is that line's
displacement at the mark's axis. Below MIN_FIT of the base's intervals on
the line, the derived letter was redrawn, and nothing is inherited for that
class in that style. Before 2026-11-11 the whole outline was matched by
translation only (outline_shift, still used for derived_y).

Letters in stem_match (bottom tails, ɗ) are matched on their stems
(stem_shift); letters in stem_axis (an l or i with a bar, belt or tilde
across the stem) take the shift between the two stems' midlines, whatever
the match.

Behavior:
    - Overwrites designer and heuristic anchors of the listed classes.
    - Never overwrites a curated anchor of the derived letter (stage 7).
    - Skips a class the base letter has no anchor for.
"""

from collections import Counter

from .font_patching_anchors import load_human_anchors
from .fontmetrics_helpers import SHIFT_K, SLOPE, get_anchor_candidate
from .fontmetrics_loader import load_fontmetrics
from .font_patching_inherit import (
    GRID_STEP,
    MIN_FIT,
    SegmentPen,
    ensure_base_record_for_glyph,
    find_mark_to_base_subtables,
    fit_base,
    fit_intervals,
    get_anchor_from_baserec,
    get_base_record_for_glyph,
    glyph_points,
    glyph_segments,
    intervals,
    set_anchor_in_baserec,
)

MIN_MATCH = 0.70  # share of the base's outline found in the derived letter
MATCH_TOL = 6     # units: a crossing within this of the shifted base matches
MARK_HALF_WIDTH = 120  # units either side of the mark's axis: a wide mark
MIN_DY = 6        # smaller differences in reach are left alone

# Letters matched on stems (stem_match in data/derived_letters.py): bottom tails, and ɗ
STEM_LO = 60      # stem fit: heights from here to the letter's top (at most XHEIGHT) minus this
XHEIGHT = 645
STEM_MAX_SCALE_DEV = 0.10  # a fitted stem scale further than this from 1 is not trusted: shift only
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

def load_stem_axis():
    """Return stem_axis from data/derived_letters.py: letters placed on their own stem midline."""
    return __import__("data.derived_letters", fromlist=["stem_axis"]).stem_axis

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

def _crossings(glyphset, glyph_name):
    """{height: sorted x of the outline crossing it}, on a fixed grid."""
    segs = glyph_segments(glyphset, glyph_name)
    ys = [y for seg in segs for _, y in seg]
    if not ys:
        return {}
    lo, hi = min(ys), max(ys)
    out = {}
    for y in range(-400, 1100, GRID_STEP):
        y += 0.5  # never exactly on a vertex
        if lo < y < hi:
            out[y] = sorted(
                x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                for (x0, y0), (x1, y1) in segs
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

def stem_shift(ttfont, font_key, derived_glyph, base_glyph, axis, max_dev=STEM_MAX_SCALE_DEV):
    """
    Return (dx, match) for a bottom-tail letter: the horizontal shift of the
    base letter inside the derived letter at the mark's axis, matched on the
    stems and bowl sides above the tail.

    fit_intervals at every height from STEM_LO to the top (at most the
    x-height) minus STEM_LO: a line x_derived = a * x_base + b through the
    centres of paired ink intervals allows for a letter drawn slightly
    narrower or wider (a is used only within STEM_MAX_SCALE_DEV of 1;
    max_dev), and dx is its shift at the axis. match is the share of the
    base's intervals within STEM_TOL of the line.
    """
    glyphset = ttfont.getGlyphSet()
    slope = SLOPE[font_key]
    sd, sb = glyph_segments(glyphset, derived_glyph), glyph_segments(glyphset, base_glyph)
    top = min(max(y for seg in s for _, y in seg) for s in (sd, sb))
    heights = range(STEM_LO, int(min(top, XHEIGHT)) - STEM_LO, GRID_STEP)
    fit = fit_intervals(sd, sb, slope, heights, max_dev)
    if fit is None:
        return 0, 0.0
    scale, offset, match = fit
    return round(scale * axis + offset - axis), match

STEM_AXIS_LO, STEM_AXIS_HI = 120, 480  # heights where the stem midline is measured
STEM_MIN_W, STEM_MAX_W = 50, 160          # an interval this wide is a stem (not a dot, bar or belt)

def stem_midline(ttfont, font_key, glyph_name):
    """
    The midline of the glyph's stem, in sheared coordinates (x - y tan):
    the median centre of the ink interval at heights where the outline has
    exactly one interval of stem width. None if fewer than 5 such heights.
    """
    glyphset = ttfont.getGlyphSet()
    segs = glyph_segments(glyphset, glyph_name)
    slope = SLOPE[font_key]
    centres = []
    for y in range(STEM_AXIS_LO, STEM_AXIS_HI, GRID_STEP):
        iv = [(a, b) for a, b in intervals(segs, slope, y + 0.5) if STEM_MIN_W <= b - a <= STEM_MAX_W]
        if len(iv) == 1:
            centres.append((iv[0][0] + iv[0][1]) / 2)
    if len(centres) < 5:
        return None
    centres.sort()
    return centres[len(centres) // 2]

def stem_axis_shift(ttfont, font_key, derived_glyph, base_glyph):
    """The shift between the base letter's stem midline and the derived letter's, or None."""
    d = stem_midline(ttfont, font_key, derived_glyph)
    b = stem_midline(ttfont, font_key, base_glyph)
    return None if d is None or b is None else round(d - b)

def _tail_reaches(ttfont, font_key, glyph_name, axis):
    """True if the outline has ink below TAIL_Y within BELOW_ZONE of the mark's axis (sheared)."""
    pts = glyph_points(ttfont.getGlyphSet(), glyph_name)
    slope = SLOPE[font_key]
    return any(y < TAIL_Y and abs(x - y * slope - axis) <= BELOW_ZONE for x, y in pts)

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

def _reach(ttfont, glyph_name, axis, slope, cls, offset=0):
    """
    Highest (above) or lowest (below) point of the outline within
    MARK_HALF_WIDTH of the mark's axis (sheared coordinates), with the
    outline moved right by offset. None if no ink there.
    """
    pts = glyph_points(ttfont.getGlyphSet(), glyph_name)
    ys = [y for x, y in pts if abs(x + offset - y * slope - axis) <= MARK_HALF_WIDTH]
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
        ys = [p[1] for p in glyph_points(ttfont.getGlyphSet(), base_glyph)]
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
    stem_axis = load_stem_axis()
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

        stem_dx = None
        if cp in stem_axis:
            stem_dx = stem_axis_shift(ttfont, font_key, derived_glyph, base_glyph)
            if stem_dx is None:
                report.append(f"{label} {derived_glyph} < {base_glyph}: no stem midline; SKIPPED")
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

            if stem_dx is not None:
                dx, how = stem_dx, f"stem midline shift {stem_dx:+d}"
            else:
                dx, match, scale = fit_base(ttfont, font_key, derived_glyph, base_glyph, cls, base_xy)
                how = f"shift {dx:+d}" + (f", scale {scale:.3f}" if abs(scale - 1) > 1e-3 else "") + f" (fit {match:.0%})"
                if match < MIN_FIT:
                    report.append(f"{label} {derived_glyph} < {base_glyph}: {name}: {how} below {MIN_FIT:.0%}; SKIPPED")
                    continue

            rec, _ = ensure_base_record_for_glyph(sub, derived_glyph)
            old = get_anchor_from_baserec(rec, cls)
            x, y, dy = inherited_anchor(ttfont, font_key, derived_glyph, base_glyph, base_xy, cls, dx)
            set_anchor_in_baserec(rec, cls, x, y)
            inherited += 1
            moved = f", y moved {dy:+d} to clear the added part" if dy else ""
            report.append(
                f"{label} {derived_glyph}: {name} anchor ({x}, {y}) from {base_glyph} "
                f"{base_xy}, {how}{moved}; was {old}"
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
