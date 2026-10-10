# anchor_audit.py
"""
Audit of the designer-set above/below base anchors in the original fonts.

Scope: every glyph with an above (class 0) or below (class 2) base anchor in
the style's mark-to-base lookup, provided the glyph has a Unicode codepoint
(small caps and alternates without one are ignored). A set of tests
classifies each anchor as "bad", "suspect" or "ok":

    side            above anchor in the lower half of the glyph, or the reverse
    inside          anchor lies in the ink of the glyph
    extent          anchor x is outside the glyph altogether
    centre          anchor x is far from the glyph's centre line
    reference       anchor y is far from every reference value
    aspect          anchor is on the reference value of an inner aspect, beside
                    an ascender or descender. This is a design choice, so it is
                    suspect; it is bad only if none of the tested marks fits there
    clearance       anchor floats far beyond the normal clearance
    collision       a common mark attached here overlaps or crowds the glyph
    copy            identical to another glyph's anchor, different letterform
    turned          turned/reversed/inverted letter whose anchor does not follow
                    the same transformation of its source letter's anchor
    style-copy      identical to the same glyph's anchor in another style
    precomposed     disagrees with where precomposed glyphs put marks
    style-position  relative position differs from the other styles

Minor y deviations (646 for 645) are left to normalization, and so are
precomposed glyphs that already carry a mark on the audited side.

All x comparisons are made in sheared coordinates (x' = x - slope*y), so the
same tests serve upright and italic styles.

Results are written by run_anchor_audit.py to data/fontanchors_audit/ and
consumed by font_patching_deleteanchors.py.
"""

from __future__ import annotations

import math
import unicodedata
from collections import defaultdict
from statistics import median

from fontTools.ttLib import TTFont
from fontTools.unicodedata import script
from fontTools.pens.recordingPen import RecordingPen

from .font_context import FONTS
from .fontmetrics_helpers import (
    ANCHOR_Y_REF_OPT,
    CLEARANCES_OPT,
    get_ideal_above_aspect,
    get_ideal_below_aspect,
    get_aya,
    get_bya,
)

# Order matters: an earlier style is presumed to be the source of a copy.
STYLE_KEYS = ["regular", "italic", "semibold", "semibold_italic"]

ABOVE, BELOW = 0, 2
SIDE_NAMES = {ABOVE: "above", BELOW: "below"}

# ----------------------------------------------------------------------
# Thresholds (font units)
# ----------------------------------------------------------------------

Y_MINOR = 6            # y deviations up to this are left to normalization
Y_GROSS = 30           # y deviation that cannot be a rounding slip
Y_ABSURD = 100         # y deviation that no letterform explains
GAP_LOOSE = 40         # clearance beyond the largest normal one: suspect
GAP_LOOSE_BAD = 120    # ... bad
GAP_LIMIT = 120        # mark-to-glyph gaps are measured up to this distance
CROWD_FRAC = 0.6       # a mark closer than this fraction of its normal gap crowds the glyph
EXTENT_MARGIN = 5      # slack before an anchor counts as outside the glyph
OFF_CENTRE_FRAC = 0.30 # off-centre by this fraction of the glyph's width: suspect
COPY_DX = 15           # a copied anchor may be this far off centre and still fit
COPY_CLUSTER_BAD = 4    # glyphs sharing an anchor before a misfit copy is bad, not suspect
COPY_DX_GROSS = 30     # a one-sided copy this far off centre is bad
TURNED_DX = 30         # turned letter's anchor this far from the transformed source anchor
LANE_TOL = 5           # widths within this: the turned glyph is a true transform of its source
PRECOMP_AGREE = 15     # anchor agrees with a precomposed glyph within this
PRECOMP_DISAGREE = 30  # anchor disagrees with every precomposed glyph by this
STYLE_FRAC = 0.15      # relative position differs from other styles by this
PROFILE_BAND = 40      # depth of one band of the letterform profile
PROFILE_BANDS = 4
PROFILE_TOL = 10

# Marks used for the collision test, by side. The first is the narrowest.
COLLISION_MARKS = {
    ABOVE: [(0x0307, "dot"), (0x0304, "macron"), (0x0302, "circumflex")],
    BELOW: [(0x0323, "dot below"), (0x0331, "macron below")],
}

# Symmetric marks: their centre in a precomposed glyph shows where the
# designer centred a mark on the base.
SYMMETRIC_MARKS = {
    0x0302, 0x0303, 0x0304, 0x0306, 0x0307, 0x0308, 0x030A, 0x030C,
    0x0323, 0x0324, 0x0325, 0x032D, 0x032E, 0x0330, 0x0331,
}

# Precomposed glyphs whose caron is drawn as an apostrophe beside the letter;
# they say nothing about where a mark is centred.
APOSTROPHE_CARON = {0x010F, 0x013D, 0x013E, 0x0165}

# Source letters that the Unicode name does not yield
TURNED_SOURCES = {0x2132: 0x0046}   # TURNED CAPITAL F

# The dot is removed before an above mark attaches, so the bbox top of
# these glyphs says nothing about the above anchor's y.
SOFT_DOTTED = {
    0x0069, 0x006A, 0x012F, 0x0249, 0x0268, 0x029D, 0x02B2, 0x03F3,
    0x0456, 0x0458, 0x1D62, 0x1D96, 0x1DA4, 0x1DA8, 0x1E2D, 0x1ECB,
    0x2071, 0x2C7C,
}

# ----------------------------------------------------------------------
# Outline geometry
# ----------------------------------------------------------------------

def _flatten(glyphset, glyph_name, line_step=10, curve_steps=12):
    """Return the glyph outline as a list of closed polylines."""
    pen = RecordingPen()
    glyphset[glyph_name].draw(pen)

    contours = []
    pts = []
    cur = None
    for op, args in pen.value:
        if op == "moveTo":
            pts = [args[0]]
            cur = args[0]
        elif op == "lineTo":
            p = args[0]
            n = max(1, int(math.hypot(p[0] - cur[0], p[1] - cur[1]) // line_step))
            for i in range(1, n + 1):
                t = i / n
                pts.append((cur[0] + (p[0] - cur[0]) * t, cur[1] + (p[1] - cur[1]) * t))
            cur = p
        elif op == "curveTo":
            p1, p2, p3 = args
            for i in range(1, curve_steps + 1):
                t = i / curve_steps
                u = 1 - t
                pts.append(tuple(
                    u**3 * cur[k] + 3 * u * u * t * p1[k] + 3 * u * t * t * p2[k] + t**3 * p3[k]
                    for k in (0, 1)
                ))
            cur = p3
        elif op in ("closePath", "endPath"):
            if len(pts) > 2:
                contours.append(pts)
            pts = []
    return contours


def _bounds(contours, slope=0.0):
    """Bounding box of the outline after shearing by -slope."""
    xs = [x - slope * y for c in contours for x, y in c]
    ys = [y for c in contours for _, y in c]
    return min(xs), min(ys), max(xs), max(ys)


def _point_in_outline(x, y, contours):
    """Even-odd test against the flattened outline (approximate)."""
    inside = False
    for pts in contours:
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
    return inside


def _outlines_overlap(base, mark, dx, dy):
    """True if the mark outline, moved by (dx, dy), overlaps the base outline."""
    moved = [[(x + dx, y + dy) for x, y in c] for c in mark]
    bx0, by0, bx1, by1 = _bounds(base)
    mx0, my0, mx1, my1 = _bounds(moved)
    if mx0 > bx1 or mx1 < bx0 or my0 > by1 or my1 < by0:
        return False

    for c in moved:
        for x, y in c:
            if bx0 <= x <= bx1 and by0 <= y <= by1 and _point_in_outline(x, y, base):
                return True
    for c in base:
        for x, y in c:
            if mx0 <= x <= mx1 and my0 <= y <= my1 and _point_in_outline(x, y, moved):
                return True
    return False


def _mark_gap(base, mark, dx, dy):
    """
    Distance between the base outline and the mark outline moved by (dx, dy):
    0 if they overlap, None if they are more than GAP_LIMIT apart.
    """
    if _outlines_overlap(base, mark, dx, dy):
        return 0
    moved = [(x + dx, y + dy) for c in mark for x, y in c]
    mx0 = min(x for x, _ in moved) - GAP_LIMIT
    mx1 = max(x for x, _ in moved) + GAP_LIMIT
    my0 = min(y for _, y in moved) - GAP_LIMIT
    my1 = max(y for _, y in moved) + GAP_LIMIT
    near = [(x, y) for c in base for x, y in c if mx0 <= x <= mx1 and my0 <= y <= my1]
    if not near:
        return None
    best = min((ax - bx) ** 2 + (ay - by) ** 2 for ax, ay in moved for bx, by in near)
    gap = math.sqrt(best)
    return gap if gap <= GAP_LIMIT else None


def _match_contours(sub, whole):
    """
    Find all contours of `sub` inside `whole` under one translation.
    Returns ((tx, ty), used_indices) or None.
    """
    if not sub:
        return None
    first = sub[0]
    for cand in whole:
        if len(cand) != len(first):
            continue
        tx = cand[0][0] - first[0][0]
        ty = cand[0][1] - first[0][1]
        used = set()
        for pts in sub:
            for j, other in enumerate(whole):
                if j in used or len(other) != len(pts):
                    continue
                if all(abs(b[0] - a[0] - tx) <= 1.01 and abs(b[1] - a[1] - ty) <= 1.01
                       for a, b in zip(pts, other)):
                    used.add(j)
                    break
            else:
                break
        else:
            return (tx, ty), used
    return None

# ----------------------------------------------------------------------
# Per-style context
# ----------------------------------------------------------------------

def _decomposition(cp):
    """(base codepoint, set of combining classes of the marks) of a codepoint."""
    nfd = unicodedata.normalize("NFD", chr(cp))
    return ord(nfd[0]), {unicodedata.combining(c) for c in nfd[1:]}


def load_style(style_key):
    """Load one font: anchors of the mark-to-base lookup, plus geometry caches."""
    meta = FONTS[style_key]
    ttfont = TTFont(meta["path"])
    cmap = ttfont.getBestCmap()

    glyph_cp = {}
    for cp, name in sorted(cmap.items()):
        glyph_cp.setdefault(name, cp)

    base_anchors = defaultdict(dict)   # glyph name -> {class: (x, y)}
    mark_anchors = {}                  # glyph name -> (class, (x, y))
    lookup = ttfont["GPOS"].table.LookupList.Lookup[meta["lookup_index"]]
    for sub in lookup.SubTable:
        if sub.LookupType != 4:
            continue
        for name, rec in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
            for cls in (ABOVE, BELOW):
                if cls < len(rec.BaseAnchor) and rec.BaseAnchor[cls] is not None:
                    a = rec.BaseAnchor[cls]
                    base_anchors[name][cls] = (a.XCoordinate, a.YCoordinate)
        for name, rec in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
            if rec.MarkAnchor is not None:
                mark_anchors[name] = (rec.Class, (rec.MarkAnchor.XCoordinate, rec.MarkAnchor.YCoordinate))

    return {
        "style": style_key,
        "glyphset": ttfont.getGlyphSet(),
        "cmap": cmap,
        "glyph_cp": glyph_cp,
        "slope": math.tan(math.radians(-ttfont["post"].italicAngle)),
        "base_anchors": base_anchors,
        "mark_anchors": mark_anchors,
        "outlines": {},
    }


def _outline(ctx, glyph_name):
    if glyph_name not in ctx["outlines"]:
        ctx["outlines"][glyph_name] = _flatten(ctx["glyphset"], glyph_name)
    return ctx["outlines"][glyph_name]


def _precomposed_evidence(ctx):
    """
    For each base glyph, the sheared x at which the font's precomposed glyphs
    centre a symmetric mark: {glyph name: {class: [x', ...]}}.
    """
    slope = ctx["slope"]
    cmap = ctx["cmap"]
    evidence = defaultdict(lambda: defaultdict(list))

    for cp, name in cmap.items():
        nfd = unicodedata.normalize("NFD", chr(cp))
        if len(nfd) != 2 or ord(nfd[1]) not in SYMMETRIC_MARKS or ord(nfd[0]) not in cmap:
            continue
        if cp in APOSTROPHE_CARON:
            continue
        ccc = unicodedata.combining(nfd[1])
        if ccc not in (230, 220):
            continue

        base_name = cmap[ord(nfd[0])]
        whole = _outline(ctx, name)
        found = _match_contours(_outline(ctx, base_name), whole)
        if not found:
            continue
        (tx, ty), used = found
        rest = [c for i, c in enumerate(whole) if i not in used]
        if not rest:
            continue

        x0, _, x1, _ = _bounds(rest, slope)
        cls = ABOVE if ccc == 230 else BELOW
        evidence[base_name][cls].append((x0 + x1) / 2 - (tx - slope * ty))

    return evidence


def _profile(ctx, glyph_name, cls):
    """
    Shape of the glyph on the anchor's side: the extreme y, and the x-extent
    in a few horizontal bands below the top (above) or above the bottom (below).
    """
    contours = _outline(ctx, glyph_name)
    _, ymin, _, ymax = _bounds(contours)
    edge = ymax if cls == ABOVE else ymin
    bands = []
    for i in range(PROFILE_BANDS):
        lo, hi = i * PROFILE_BAND, (i + 1) * PROFILE_BAND
        xs = [x for c in contours for x, y in c if lo <= abs(edge - y) < hi]
        bands.append((min(xs), max(xs)) if xs else None)
    return edge, bands


def _same_letterform(ctx, glyph_a, glyph_b, cls):
    """True if two glyphs have the same shape on the anchor's side."""
    edge_a, bands_a = _profile(ctx, glyph_a, cls)
    edge_b, bands_b = _profile(ctx, glyph_b, cls)
    if abs(edge_a - edge_b) > PROFILE_TOL:
        return False
    for a, b in zip(bands_a, bands_b):
        if (a is None) != (b is None):
            return False
        if a and (abs(a[0] - b[0]) > PROFILE_TOL or abs(a[1] - b[1]) > PROFILE_TOL):
            return False
    return True

# ----------------------------------------------------------------------
# Pass 1: collect every audited anchor with its measurements
# ----------------------------------------------------------------------

def _has_latin_aspects(cp):
    """
    True if the reference values apply: Latin, Greek and Cyrillic letters.
    Modifier letters and other scripts have their own vertical aspects.
    """
    if unicodedata.category(chr(cp)) not in ("Lu", "Ll", "Lo"):
        return False
    return script(chr(cp)) in ("Latn", "Grek", "Cyrl")


def _collect(ctx):
    """Return {(glyph name, class): entry} for the anchors in scope."""
    slope = ctx["slope"]
    evidence = _precomposed_evidence(ctx)
    entries = {}

    for name, by_class in ctx["base_anchors"].items():
        cp = ctx["glyph_cp"].get(name)
        if cp is None:
            continue
        contours = _outline(ctx, name)
        if not contours:
            continue
        _, marks_ccc = _decomposition(cp)

        xmin, ymin, xmax, ymax = _bounds(contours)
        sx0, _, sx1, _ = _bounds(contours, slope)
        width = sx1 - sx0

        for cls, (x, y) in by_class.items():
            # precomposed glyph that already carries a mark on this side:
            # its anchor is a normalization matter
            if (cls == ABOVE and 230 in marks_ccc) or (cls == BELOW and 220 in marks_ccc):
                continue

            xs = x - slope * y
            entries[(name, cls)] = {
                "glyph": name,
                "cp": cp,
                "cls": cls,
                "xy": (x, y),
                "bbox": (xmin, ymin, xmax, ymax),
                "lane": (sx0, sx1),
                "dx": xs - (sx0 + sx1) / 2,          # offset from the centre line
                "frac": (xs - sx0) / width if width else 0.5,
                "centre_x": (sx0 + sx1) / 2 + slope * y,
                "evidence": [e - xs for e in evidence[name][cls]],   # precomposed minus anchor
                "findings": [],
            }
    return entries

# ----------------------------------------------------------------------
# Pass 2: tests. Each appends (level, key, text) to entry["findings"].
# ----------------------------------------------------------------------

def _flag(entry, level, key, text):
    entry["findings"].append((level, key, text))


def _explained_by_precomposed(entry):
    return any(abs(d) <= PRECOMP_AGREE for d in entry["evidence"])


def _test_side(ctx, entry):
    y = entry["xy"][1]
    _, ymin, _, ymax = entry["bbox"]
    middle = (ymin + ymax) / 2
    if entry["cls"] == ABOVE and y < middle:
        _flag(entry, "bad", "side", f"above anchor at y = {y}, in the lower half of the glyph or below it")
    elif entry["cls"] == BELOW and y > middle:
        _flag(entry, "bad", "side", f"below anchor at y = {y}, in the upper half of the glyph or above it")


def _test_inside(ctx, entry):
    x, y = entry["xy"]
    if _point_in_outline(x, y, _outline(ctx, entry["glyph"])):
        _flag(entry, "bad", "inside", "anchor lies inside the glyph's outline")


def _test_extent_and_centre(ctx, entry):
    sx0, sx1 = entry["lane"]
    xs = entry["xy"][0] - ctx["slope"] * entry["xy"][1]
    if xs < sx0 - EXTENT_MARGIN or xs > sx1 + EXTENT_MARGIN:
        side = "left" if xs < sx0 else "right"
        dist = sx0 - xs if xs < sx0 else xs - sx1
        _flag(entry, "bad", "extent", f"anchor x is {dist:.0f} outside the glyph, to the {side}")
    elif abs(entry["dx"]) > OFF_CENTRE_FRAC * (sx1 - sx0) and not _explained_by_precomposed(entry):
        _flag(entry, "suspect", "centre",
              f"anchor x is {entry['dx']:+.0f} from the centre line ({abs(entry['dx']) / (sx1 - sx0):.0%} of the width)")


def _test_reference_and_clearance(ctx, entry):
    style = ctx["style"]
    cls = entry["cls"]
    y = entry["xy"][1]
    _, ymin, _, ymax = entry["bbox"]
    refs = ANCHOR_Y_REF_OPT[style]
    clear = CLEARANCES_OPT[style]

    if not _has_latin_aspects(entry["cp"]):
        return
    if cls == ABOVE:
        if entry["cp"] in SOFT_DOTTED:
            return
        aspect = get_ideal_above_aspect(style, round(ymax), entry["cp"])
        candidate = get_aya(style, aspect)
        ref_values = [refs["asc"], refs["cap"], refs["xh"]]
        gap = y - ymax
        max_clear = max(clear["asc"], clear["cap"], clear["xh"])
    else:
        aspect = get_ideal_below_aspect(style, round(ymin))
        candidate = get_bya(style, aspect)
        ref_values = [refs["base"], refs["desc"]]
        gap = ymin - y
        max_clear = max(clear["base"], clear["desc"])

    snapped = len(aspect) == 1
    d_ref = min(abs(y - r) for r in ref_values)

    if d_ref > Y_MINOR:
        dev = min(d_ref, abs(y - candidate))
        if dev >= Y_ABSURD:
            _flag(entry, "bad", "reference", f"y = {y} is {dev:.0f} from every reference value")
        elif snapped and dev >= Y_GROSS:
            _flag(entry, "bad", "reference",
                  f"y = {y} is {dev:.0f} from every reference value although the glyph sits on aspect '{aspect}'")
        elif snapped and dev > Y_MINOR:
            _flag(entry, "suspect", "reference",
                  f"y = {y} is {dev:.0f} from the nearest reference value (aspect '{aspect}')")
        elif not snapped and dev >= Y_GROSS:
            _flag(entry, "suspect", "reference",
                  f"y = {y} is {dev:.0f} from both the reference values and the clearance rule (aspect '{aspect}')")
        return

    # on a reference value, but that of an inner aspect: the anchor sits
    # beside an ascender or descender instead of beyond it
    if snapped and abs(y - candidate) > Y_MINOR and gap < 0:
        part = "top" if cls == ABOVE else "bottom"
        tested, fit = entry["marks_tested"], entry["marks_fit"]
        level = "bad" if tested and fit == 0 else "suspect"
        _flag(entry, level, "aspect",
              f"glyph sits on aspect '{aspect}' but y = {y} is the reference of an inner aspect, "
              f"{-gap:.0f} inside the {part} of the glyph; {fit} of {tested} tested marks fit there")
        return

    excess = gap - max_clear
    if excess > GAP_LOOSE_BAD:
        _flag(entry, "bad", "clearance",
              f"anchor is {gap:.0f} clear of the glyph; the largest normal clearance is {max_clear}")
    elif excess > GAP_LOOSE:
        _flag(entry, "suspect", "clearance",
              f"anchor is {gap:.0f} clear of the glyph; the largest normal clearance is {max_clear}")


def _measure_mark_gaps(ctx, entry):
    """Store entry["mark_gaps"]: {mark label: gap} for the collision marks."""
    cls = entry["cls"]
    x, y = entry["xy"]
    base = _outline(ctx, entry["glyph"])
    entry["mark_gaps"] = {}
    for mark_cp, label in COLLISION_MARKS[cls]:
        mark_name = ctx["cmap"].get(mark_cp)
        if mark_name not in ctx["mark_anchors"]:
            continue
        mark_cls, (mx, my) = ctx["mark_anchors"][mark_name]
        if mark_cls != cls:
            continue
        entry["mark_gaps"][label] = _mark_gap(base, _outline(ctx, mark_name), x - mx, y - my)


def _crowding_applies(entry):
    """
    Crowding is judged only where the ordinary mark shapes and clearances
    apply: not modifier letters or other scripts, and above, not capitals
    (which take the flatter .cap marks) or soft-dotted letters (which lose
    their dot).
    """
    cp = entry["cp"]
    if not _has_latin_aspects(cp):
        return False
    if entry["cls"] == ABOVE and (unicodedata.category(chr(cp)) == "Lu" or cp in SOFT_DOTTED):
        return False
    return True


def _normal_gaps(entries):
    """Median gap per (class, mark label) over the anchors whose mark does not overlap."""
    samples = defaultdict(list)
    for e in entries.values():
        if not _crowding_applies(e):
            continue
        for label, gap in e["mark_gaps"].items():
            if gap != 0:
                samples[(e["cls"], label)].append(GAP_LIMIT if gap is None else gap)
    return {key: median(values) for key, values in samples.items()}


def _test_collisions(ctx, entry, normal):
    cls = entry["cls"]
    gaps = entry["mark_gaps"]
    hits = [label for label, gap in gaps.items() if gap == 0]
    if cls == ABOVE and entry["cp"] in SOFT_DOTTED:
        hits = []
    crowded = [
        (label, gap) for label, gap in gaps.items()
        if gap and (cls, label) in normal and gap < CROWD_FRAC * normal[(cls, label)]
    ] if _crowding_applies(entry) else []
    # how many of the tested marks fit: neither overlapping nor crowded
    entry["marks_tested"] = len(gaps)
    entry["marks_fit"] = len(gaps) - len(set(hits) | {label for label, _ in crowded})

    if hits:
        narrowest = COLLISION_MARKS[cls][0][1]
        level = "bad" if narrowest in hits else "suspect"
        _flag(entry, level, "collision",
              f"{', '.join(hits)} overlap{'s' if len(hits) == 1 else ''} the glyph "
              f"({len(hits)} of {len(gaps)} marks tested)")
    elif crowded:
        text = ", ".join(f"{label} {gap:.0f} from the glyph (normally {normal[(cls, label)]:.0f})"
                         for label, gap in crowded)
        _flag(entry, "suspect", "collision", f"crowded: {text}")


def _owner_rank(entry):
    # plain ASCII letters first, then by codepoint
    return (entry["cp"] >= 0x80, entry["cp"])


def _test_copies_within_style(ctx, entries):
    """Anchors identical to another glyph's, on a different letterform."""
    by_x = defaultdict(list)
    for e in entries.values():
        by_x[(e["cls"], e["xy"][0])].append(e)

    for (cls, _), group in by_x.items():
        group.sort(key=lambda e: e["xy"][1])
        clusters = [[group[0]]]
        for e in group[1:]:
            if e["xy"][1] - clusters[-1][-1]["xy"][1] <= 2:
                clusters[-1].append(e)
            else:
                clusters.append([e])

        for cluster in clusters:
            if len(cluster) < 2:
                continue
            owner = min(cluster, key=_owner_rank)
            owner_base, _ = _decomposition(owner["cp"])
            for e in cluster:
                if e is owner:
                    continue
                base, _ = _decomposition(e["cp"])
                if base == owner_base or base == owner["cp"] or owner_base == e["cp"]:
                    continue
                if _same_letterform(ctx, owner["glyph"], e["glyph"], cls):
                    continue
                if abs(e["dx"]) <= COPY_DX or _explained_by_precomposed(e):
                    continue

                # careless copies usually take the whole record: is the
                # anchor on the other side the owner's too?
                other_e = entries.get((e["glyph"], 2 - cls))
                other_o = entries.get((owner["glyph"], 2 - cls))
                both = bool(other_e and other_o and other_e["xy"][0] == other_o["xy"][0]
                            and abs(other_e["xy"][1] - other_o["xy"][1]) <= 2)

                big = len(cluster) >= COPY_CLUSTER_BAD
                level = "bad" if both or (big and abs(e["dx"]) > COPY_DX_GROSS) else "suspect"
                others = f" and {len(cluster) - 2} other(s)" if len(cluster) > 2 else ""
                record = ", as is its other anchor" if both else ""
                _flag(e, level, "copy",
                      f"same anchor as {chr(owner['cp'])} (U+{owner['cp']:04X}){others}{record}, "
                      f"a different letterform; {e['dx']:+.0f} from this glyph's centre line")


def _turned_source(cp):
    """
    (kind, source codepoint) if the character is a turned, reversed or
    inverted form of another letter, judged by its Unicode name.
    """
    name = unicodedata.name(chr(cp), "")
    head = name.split(" WITH ")[0]
    for kind in ("TURNED", "REVERSED", "INVERTED"):
        if kind + " " not in head:
            continue
        if cp in TURNED_SOURCES:
            return kind, TURNED_SOURCES[cp]
        try:
            return kind, ord(unicodedata.lookup(name.replace(kind + " ", "", 1)))
        except KeyError:
            return None, None
    return None, None


def _test_turned(ctx, entries):
    """
    A turned letter is its source rotated by 180 degrees, so its above anchor
    should mirror the source's below anchor. A reversed letter mirrors the
    source's anchor on the same side; an inverted one takes the x of the
    opposite side. Compared in sheared coordinates.
    """
    slope = ctx["slope"]
    for e in entries.values():
        kind, source_cp = _turned_source(e["cp"])
        source_name = ctx["cmap"].get(source_cp) if source_cp else None
        if not source_name:
            continue
        cls = e["cls"]
        s_same = entries.get((source_name, cls))
        s_from = s_same if kind == "REVERSED" else entries.get((source_name, 2 - cls))
        if not s_from or any(level == "bad" for level, _, _ in s_from["findings"]):
            continue
        if abs((e["lane"][1] - e["lane"][0]) - (s_from["lane"][1] - s_from["lane"][0])) > LANE_TOL:
            continue

        xs = e["xy"][0] - slope * e["xy"][1]
        src_xs = s_from["xy"][0] - slope * s_from["xy"][1]
        if kind == "INVERTED":
            expected = src_xs + e["lane"][0] - s_from["lane"][0]
        else:
            expected = e["lane"][0] + s_from["lane"][1] - src_xs
        diff = xs - expected
        source = f"{chr(source_cp)} (U+{source_cp:04X})"

        unchanged = (s_same and e["xy"][0] == s_same["xy"][0]
                     and abs(e["xy"][1] - s_same["xy"][1]) <= 2)
        if unchanged and abs(diff) > COPY_DX:
            _flag(e, "bad", "turned",
                  f"{kind.lower()} form of {source} but carries that letter's anchor unchanged; "
                  f"{diff:+.0f} from where the transformation puts it")
        elif abs(diff) > TURNED_DX:
            _flag(e, "suspect", "turned",
                  f"{kind.lower()} form of {source}; anchor x is {diff:+.0f} from the transformed anchor of that letter")


def _test_across_styles(all_entries):
    """Copies between styles, and relative positions that disagree between styles."""
    for i, style in enumerate(STYLE_KEYS):
        for key, e in all_entries[style].items():
            # identical to an earlier style's anchor, and a worse fit here
            for earlier in STYLE_KEYS[:i]:
                o = all_entries[earlier].get(key)
                if not o or o["xy"][0] != e["xy"][0] or abs(o["xy"][1] - e["xy"][1]) > 2:
                    continue
                shift = e["centre_x"] - o["centre_x"]
                if (abs(shift) > COPY_DX and abs(e["dx"]) - abs(o["dx"]) > COPY_DX
                        and not _explained_by_precomposed(e)):
                    _flag(e, "bad", "style-copy",
                          f"identical to the {earlier.replace('_', ' ')} anchor, but this glyph's centre line is "
                          f"{shift:+.0f} from that style's; {e['dx']:+.0f} off centre here ({o['dx']:+.0f} there)")
                break

    # relative position against the other styles' anchors that are not bad
    clean = {
        style: {key: e["frac"] for key, e in all_entries[style].items()
                if not any(level == "bad" for level, _, _ in e["findings"])}
        for style in STYLE_KEYS
    }
    for style in STYLE_KEYS:
        for key, e in all_entries[style].items():
            others = [clean[s][key] for s in STYLE_KEYS if s != style and key in clean[s]]
            if len(others) < 2:
                continue
            # flag only the less centred side of a disagreement
            if (abs(e["frac"] - median(others)) > STYLE_FRAC
                    and abs(e["frac"] - 0.5) > abs(median(others) - 0.5)):
                _flag(e, "suspect", "style-position",
                      f"anchor sits {e['frac']:.0%} across the glyph; {median(others):.0%} in the other styles")


def _test_precomposed(entry):
    if not entry["evidence"]:
        return
    nearest = min(entry["evidence"], key=abs)
    if abs(nearest) > PRECOMP_DISAGREE:
        _flag(entry, "suspect", "precomposed",
              f"precomposed glyphs centre marks {nearest:+.0f} from this anchor "
              f"({len(entry['evidence'])} glyph(s) compared)")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

def audit_all_styles():
    """
    Run every test on every style.

    Returns {style: {(glyph name, class): entry}}; each entry carries
    "verdict" ("bad", "suspect" or "ok") and "findings", a list of
    (level, test key, text).
    """
    contexts = {style: load_style(style) for style in STYLE_KEYS}
    all_entries = {style: _collect(contexts[style]) for style in STYLE_KEYS}

    for style in STYLE_KEYS:
        ctx = contexts[style]
        entries = all_entries[style]
        for e in entries.values():
            _measure_mark_gaps(ctx, e)
        normal = _normal_gaps(entries)
        for e in entries.values():
            _test_side(ctx, e)
            _test_inside(ctx, e)
            _test_extent_and_centre(ctx, e)
            _test_collisions(ctx, e, normal)
            _test_reference_and_clearance(ctx, e)
            _test_precomposed(e)
        _test_copies_within_style(ctx, entries)
        _test_turned(ctx, entries)

    _test_across_styles(all_entries)

    for entries in all_entries.values():
        for e in entries.values():
            levels = {level for level, _, _ in e["findings"]}
            e["verdict"] = "bad" if "bad" in levels else "suspect" if "suspect" in levels else "ok"

    return all_entries
