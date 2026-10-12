# font_patching_capmarks.py
"""
Capital-mark anchor stage of the Libertinus patching pipeline.

Sets the mark anchor of each capital form of an above mark (grave.cap,
acute.cap, ...), using the designer's precomposed capitals as the guide.

For each capital form, the mark's contours are found inside every
precomposed glyph that is a capital A-Z plus that one mark. That gives, per
precomposed glyph, how far the mark was moved from its own glyph.

    y   the capital anchor reference height (CAP_ANCHOR_Y) minus the
        vertical move, median over the precomposed glyphs. Attached to a
        capital whose above-anchor is at the reference height, the mark
        then sits at the height it has in the precomposed glyphs.

    x   a symmetric mark: the centre of its outline on its own axis,
        X = C + Y tan(theta), as in the anchor model.
        An asymmetric mark (ASYMMETRIC): the median, over the precomposed
        glyphs, of where the mark sits relative to the midline of the base,
        W/2 + Y tan(theta).
        In semibold italic both are moved left by K, as in the semibold
        italic anchor model.

The x of an asymmetric mark assumes that the above-anchor of a capital is on
the midline of its lane. Where the designer's capital anchors are not, the
mark is displaced by the same amount.

This stage runs before the human-curated anchors, which overrule it.
"""

import math
import statistics
import unicodedata

from fontTools.pens.recordingPen import RecordingPen

from .font_patching_addmarks import _mark_anchor, _set_mark_anchor

ABOVE = 0

# Combining mark -> its capital form.
CAP_MARKS = {
    0x0300: "grave.cap",
    0x0301: "acute.cap",
    0x0302: "circumflex.cap",
    0x0306: "breve.cap",
    0x0307: "dotaccent.cap",
    0x0308: "dieresis.cap",
    0x0309: "hookabovecomb.cap",
    0x030B: "hungarumlaut.cap",
    0x030C: "caron.cap",
    0x030F: "uni030F.cap",
    0x0311: "breveinvertedcmb.cap",
}

# Marks whose optical centre is not the centre of the outline.
ASYMMETRIC = {"grave.cap", "acute.cap", "hungarumlaut.cap", "uni030F.cap"}

# Above-anchor reference height of capitals (semibold is 805 by design).
CAP_ANCHOR_Y = {"regular": 850, "italic": 850, "semibold": 805, "semibold_italic": 850}

SLOPE = {
    "regular": 0.0,
    "italic": math.tan(math.radians(12)),
    "semibold": 0.0,
    "semibold_italic": math.tan(math.radians(11.5)),
}

# Semibold italic anchor model: anchors are left of the axis by this shift.
SHIFT_K = {"regular": 0, "italic": 0, "semibold": 0, "semibold_italic": 150}


# ------------------------------------------------------------
# Outlines
# ------------------------------------------------------------

def _contours(glyphset, glyph_name):
    """Contours of a glyph as lists of points (control points included)."""
    pen = RecordingPen()
    glyphset[glyph_name].draw(pen)
    contours, current = [], []
    for operator, operands in pen.value:
        if operator in ("closePath", "endPath"):
            if current:
                contours.append(current)
            current = []
        else:
            current.extend(operands)
    return contours


def _find(mark, whole):
    """Translation (tx, ty) that puts every contour of `mark` on one of `whole`, or None."""
    if not mark:
        return None
    first = mark[0]
    for candidate in whole:
        if len(candidate) != len(first):
            continue
        tx, ty = candidate[0][0] - first[0][0], candidate[0][1] - first[0][1]
        used = set()
        for points in mark:
            for index, other in enumerate(whole):
                if index in used or len(other) != len(points):
                    continue
                if all(abs(b[0] - a[0] - tx) <= 1.01 and abs(b[1] - a[1] - ty) <= 1.01
                       for a, b in zip(points, other)):
                    used.add(index)
                    break
            else:
                break
        else:
            return tx, ty
    return None


def _axis(contours, slope):
    """Where the axis of the outline meets the baseline: its centre, unslanted."""
    xs = [x - slope * y for points in contours for x, y in points]
    return (min(xs) + max(xs)) / 2


# ------------------------------------------------------------
# Stage
# ------------------------------------------------------------

def cap_mark_anchors(ttfont, font_key):
    """
    The anchor of each capital form: {glyph name: details}, where details
    has x, y, the number of precomposed glyphs used, the spread of their
    implied x, and the precomposed capitals that did not match.
    """
    slope = SLOPE[font_key]
    reference_y = CAP_ANCHOR_Y[font_key]
    shift = SHIFT_K[font_key]
    glyphset = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()
    hmtx = ttfont["hmtx"]

    results = {}
    for mark_cp, cap_name in CAP_MARKS.items():
        if cap_name not in glyphset:
            continue
        mark = _contours(glyphset, cap_name)

        moves, bases, unmatched = [], [], []
        for cp, glyph_name in sorted(cmap.items()):
            decomposition = unicodedata.normalize("NFD", chr(cp))
            if (len(decomposition) != 2 or ord(decomposition[1]) != mark_cp
                    or not "A" <= decomposition[0] <= "Z"):
                continue
            move = _find(mark, _contours(glyphset, glyph_name))
            if move is None:
                unmatched.append(decomposition[0])
                continue
            moves.append((move, hmtx[glyph_name][0]))
            bases.append(decomposition[0])
        if not moves:
            continue

        y = statistics.median(reference_y - ty for (_, ty), _ in moves)
        implied_x = sorted(width / 2 + slope * reference_y - shift - tx
                           for (tx, _), width in moves)
        if cap_name in ASYMMETRIC:
            x = statistics.median(implied_x)
        else:
            x = _axis(mark, slope) + slope * y - shift

        results[cap_name] = {
            "x": round(x),
            "y": round(y),
            "bases": "".join(bases),
            "implied_x": (round(implied_x[0]), round(statistics.median(implied_x)), round(implied_x[-1])),
            "unmatched": "".join(unmatched),
        }
    return results


def patch_cap_mark_anchors(ttfont, font_key, lookup_index):
    """Set the mark anchor of every capital form. Returns a report."""
    report = []
    for cap_name, found in cap_mark_anchors(ttfont, font_key).items():
        before = _mark_anchor(ttfont, lookup_index, cap_name)
        _set_mark_anchor(ttfont, lookup_index, cap_name, ABOVE, (found["x"], found["y"]))
        low, median, high = found["implied_x"]
        line = (
            f"{cap_name}: anchor ({found['x']}, {found['y']}), was {before[1] if before else None}; "
            f"from {len(found['bases'])} precomposed ({found['bases']}), "
            f"implied x {low}..{high}, median {median}"
        )
        if found["unmatched"]:
            line += f"; not matched: {found['unmatched']}"
        report.append(line)
    return report
