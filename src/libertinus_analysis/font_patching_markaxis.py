# font_patching_markaxis.py
"""
Mark-axis rule for symmetric above marks, part of stage 4 of the patching
pipeline (after the capital-mark anchors).

A symmetric above mark has its anchor on its own axis: k = K, where

    k = C + Y tan(theta) - X

is the centre of the mark's outline on its axis (C, where the axis meets the
baseline) at the anchor's height, minus the anchor's X; and K is the style's
shift (0, or 150 in semibold italic; ANCHOR-HEURISTICS.md §3). The rule moves
the anchor's X only, and only where |k - K| >= THRESHOLD: smaller deviations
are within the designer's own spread, and moving them gained nothing (the
mark-snap test of 2026-11-08 moved every mark and made as many worse against
the precomposed glyphs as better).

Adopted 2026-11-09 (report, "Mark anchor model"): for symmetric marks the
model, not the precomposed glyphs, decides X. What a composed mark then still
differs from the designer's precomposed glyphs by (in semibold italic about
+12 to +16 for every mark) is common to the marks of a style and so a matter
for the base anchors, not for each mark. Asymmetric marks (grave, acute,
double acute, double grave) keep their designed k. Mark anchor Y is not
touched here.

Since 2026-11-12 the rule also covers the mirror-symmetric below marks
(SYMMETRIC_BELOW), with K = -12 in semibold italic (SHIFT_K_BELOW), and has
no threshold (THRESHOLD = 0); the tacks keep their decided placement.

k is measured on the mark's ink (its bounds with the slant removed). With the
threshold of 10 the rule moves 37 anchors (2026-11-09), among them italic tilde
(k 11), semibold dieresis (12), semibold italic tilde (139) and dieresis (112),
the vertical tilde and perispomeni (about 18) in the upright styles, and most
of semibold italic's combining letters (k 130-140). What is left is under 10
(the ring: +2, +3, 0, +7); whether to go lower is open (test sheet
mark_threshold_test_sheet).

A mark with a curated anchor (stage 7, data/fontanchors_human/{style}.py) is
skipped here, so that an anchor is set in one place only: the curated value is
the final anchor, and should itself obey the rule. The stage reports a curated
anchor that does not.
"""

import math

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.pens.transformPen import TransformPen

from .font_patching_addmarks import _mark_anchor, _set_mark_anchor
from .font_patching_anchors import load_human_anchors
from .font_patching_capmarks import SHIFT_K
from .font_patching_inherit import stem_line

ABOVE = 0
BELOW = 2
THRESHOLD = 0

SLOPE = {
    "regular": 0.0,
    "italic": math.tan(math.radians(12)),
    "semibold": 0.0,
    "semibold_italic": math.tan(math.radians(11.5)),
}

# Symmetric above marks: mirror-symmetric outlines (their area centroid within 0.5% of
# their width of the centre in regular), plus the combining Latin letters, centred on
# their ink as base letters are. Left out as designed asymmetric, with their own k: grave,
# acute, the grave and acute tone marks, double acute and double grave (a symmetric
# pair placed off-centre), hook above, the comma-shaped marks (U+0312-U+0314, koronis
# U+0343), the half rings (U+0351, U+0357) and the right arrowhead (U+0350).
SYMMETRIC_ABOVE = {
    0x0302: "circumflex",
    0x0303: "tilde",
    0x0304: "macron",
    0x0306: "breve",
    0x0307: "dot above",
    0x0308: "dieresis",
    0x030A: "ring above",
    0x030C: "caron",
    0x030D: "vertical line above",
    0x030E: "double vertical line above",
    0x0310: "candrabindu",
    0x0311: "inverted breve",
    0x033D: "x above",
    0x033E: "vertical tilde",
    0x033F: "double overline",
    0x0342: "perispomeni",
    0x0346: "bridge above",
    0x034A: "not tilde above",
    0x034B: "homothetic above",
    0x034C: "almost equal to above",
    0x0352: "fermata",
    0x035B: "zigzag above",
}
COMBINING_LETTERS = {0x0363: "a", 0x0364: "e", 0x0365: "i", 0x0366: "o", 0x0367: "u", 0x0368: "c",
                     0x0369: "d", 0x036A: "h", 0x036B: "m", 0x036C: "r", 0x036D: "t", 0x036E: "v",
                     0x036F: "x"}
SYMMETRIC_ABOVE.update({cp: f"combining letter {letter}" for cp, letter in COMBINING_LETTERS.items()})

# Symmetric below marks (2026-11-12): the mirror-symmetric ones. Left out: the tacks U+0318 U+0319
# U+031D U+031E (decided: centred on the whole outline, or X along the slant), grave and acute below,
# the half rings, comma below and left angle below (asymmetric), and the attached marks (other classes).
SYMMETRIC_BELOW = {
    0x031F: "plus sign below",
    0x0320: "minus sign below",
    0x0323: "dot below",
    0x0324: "diaeresis below",
    0x0325: "ring below",
    0x0329: "vertical line below",
    0x032A: "bridge below",
    0x032B: "inverted double arch below",
    0x032C: "caron below",
    0x032D: "circumflex below",
    0x032E: "breve below",
    0x032F: "inverted breve below",
    0x0330: "tilde below",
    0x0331: "macron below",
    0x0333: "double low line",
    0x033A: "inverted bridge below",
    0x033B: "square below",
    0x033C: "seagull below",
    0x0347: "equals sign below",
    0x0348: "double vertical line below",
    0x034D: "left right arrow below",
    0x034E: "upwards arrow below",
}
# K of the below marks: semibold italic draws them, as its base anchors, 12 right of the axis.
SHIFT_K_BELOW = {"regular": 0, "italic": 0, "semibold": 0, "semibold_italic": -12}

# How the axis of a mark is measured, where it is not the centre of its bounds ("bbox").
# The combining letters that are not boxy (2026-11-12): bbox and area centroid more than
# about 4 apart in regular (r 11, c 9, h 8, e 6, t 4). Their axis is the area centroid,
# which weights the stems over a thin arm, terminal or open side; combining i is
# measured on its stem, which its left top serif pulls the bounds 2.6 off.
# Boxy enough for the bounds: a, d, m, o, u, v, x (bounds and centroid within 3).
AXIS_MEASURE = {
    0x0364: "centroid",  # e
    0x0365: "stem",      # i
    0x0368: "centroid",  # c
    0x036A: "centroid",  # h
    0x036C: "centroid",  # r
    0x036D: "centroid",  # t
}


def ink_axis(glyphset, glyph_name, slope, measure="bbox"):
    """
    Where the mark's axis meets the baseline, with the slant removed:
        bbox      the centre of its bounds;
        centroid  the centre of its ink area;
        stem      the midline of its stem at the stem's top, carried down at the slant.
    """
    deslant = (1, 0, -slope, 1, 0, 0)
    if measure == "centroid":
        pen = StatisticsPen(glyphset)
        glyphset[glyph_name].draw(TransformPen(pen, deslant))
        return pen.meanX
    pen = BoundsPen(glyphset)
    glyphset[glyph_name].draw(TransformPen(pen, deslant))
    xmin, ymin, xmax, ymax = pen.bounds
    if measure == "stem":
        found = stem_line(glyphset, glyph_name)
        if found is None:
            raise ValueError(f"{glyph_name}: no stem found")
        midline, _, y_top = found
        return midline(y_top) - slope * y_top
    return (xmin + xmax) / 2


def mark_shift(glyphset, glyph_name, anchor, slope, measure="bbox"):
    """k of a mark: the centre of its ink on its axis, at the anchor's height, minus the anchor's X."""
    x, y = anchor
    return ink_axis(glyphset, glyph_name, slope, measure) + slope * y - x


def patch_mark_axis(ttfont, font_key, lookup_index, threshold=THRESHOLD, skip_curated=True):
    """Move the anchor X of each symmetric above and below mark with |k - K| >= threshold to k = K."""
    glyphset = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()
    slope = SLOPE[font_key]
    human = load_human_anchors(font_key) if skip_curated else {}
    report = []
    for cls, marks, target in ((ABOVE, SYMMETRIC_ABOVE, SHIFT_K[font_key]),
                               (BELOW, SYMMETRIC_BELOW, SHIFT_K_BELOW[font_key])):
        side = "above" if cls == ABOVE else "below"
        for codepoint, name in marks.items():
            glyph_name = cmap.get(codepoint)
            curated = (human.get("marks", {}).get(codepoint, {}).get(cls)
                       or human.get("marks_by_name", {}).get(glyph_name, {}).get(cls))
            if curated is not None:
                k = mark_shift(glyphset, glyph_name, curated, slope, AXIS_MEASURE.get(codepoint, "bbox"))
                off = abs(k - target) >= threshold and round(curated[0] + k - target) != curated[0]
                verdict = (f"k {k:.1f}, {abs(k - target):.1f} off the rule (X {curated[0] + k - target:.1f}); CHECK"
                           if off else "obeys the rule")
                report.append(f"U+{codepoint:04X} {name}: curated anchor {curated} (stage 7), {verdict}; skipped")
                continue
            found = _mark_anchor(ttfont, lookup_index, glyph_name) if glyph_name else None
            if found is None or found[0] != cls:
                report.append(f"U+{codepoint:04X} {name}: no {side} mark anchor; SKIPPED")
                continue
            _, (x, y) = found
            k = mark_shift(glyphset, glyph_name, (x, y), slope, AXIS_MEASURE.get(codepoint, "bbox"))
            new_x = round(x + k - target)
            if abs(k - target) < threshold or new_x == x:
                continue
            _set_mark_anchor(ttfont, lookup_index, glyph_name, cls, (new_x, y))
            report.append(f"U+{codepoint:04X} {name} {glyph_name}: k {k:.0f} -> {target}; "
                          f"anchor ({x}, {y}) -> ({new_x}, {y}), the mark moves {abs(new_x - x)} "
                          f"{'right' if new_x < x else 'left'}")
    return report
