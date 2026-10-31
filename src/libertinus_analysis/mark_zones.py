# mark_zones.py
"""
Mark outline zones: one TikZ figure per style, overlaying the outlines of the
above and below marks on a solid o, each mark placed on o's anchor for its
class, so that it sits where the shaper puts it. Read from the patched fonts.

The grid is in font units of the o. The common marks (MARK_COMMON) are black
outlines; the others are gray with a light fill, so that the fill builds up
into the zone and the common outlines stay legible on it.
"""

import math

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from data.ipa.ipa_unicode import MARK_ABOVE, MARK_BELOW, MARK_COMMON
from .font_context import FONTS, extract_mark_attachment_data

STYLE_KEYS = ["regular", "italic", "semibold", "semibold_italic"]

ABOVE = 0
BELOW = 2

BASE = "o"

# 3 x the 0.075 of the anchor model figures.
SCALE = 0.225

GRID = 100
LABEL_EVERY = 200
Y_RANGE = (-300, 800)


def _number(value):
    return f"{round(value, 1):g}"


def _point(point, dx, dy):
    return f"({_number(point[0] + dx)},{_number(point[1] + dy)})"


def _outline(glyphset, glyph_name, dx=0, dy=0):
    """A TikZ path for the glyph's outline, moved by (dx, dy)."""
    pen = RecordingPen()
    glyphset[glyph_name].draw(pen)
    path = []
    for operator, operands in pen.value:
        if operator == "moveTo":
            path.append(_point(operands[0], dx, dy))
        elif operator == "lineTo":
            path.append("-- " + _point(operands[0], dx, dy))
        elif operator == "curveTo":
            a, b, c = (_point(p, dx, dy) for p in operands)
            path.append(f".. controls {a} and {b} .. {c}")
        elif operator == "closePath":
            path.append("-- cycle")
    return " ".join(path)


def _placed_marks(ttfont, anchors, codepoints, anchor_class):
    """
    (glyph name, dx, dy, codepoint) for each mark of the class: the move that
    puts the mark's anchor on the base's anchor.
    """
    cmap = ttfont.getBestCmap()
    base_anchor = anchors[BASE][anchor_class]
    placed = []
    for codepoint in codepoints:
        glyph_name = cmap.get(codepoint)
        mark_anchor = anchors.get(glyph_name, {}).get(anchor_class)
        if mark_anchor is None:
            continue
        placed.append((glyph_name,
                       base_anchor.XCoordinate - mark_anchor.XCoordinate,
                       base_anchor.YCoordinate - mark_anchor.YCoordinate,
                       codepoint))
    return placed


def _x_range(ttfont, glyphset, marks):
    xs = []
    for glyph_name, dx, _, _ in marks + [(BASE, 0, 0, None)]:
        pen = RecordingPen()
        glyphset[glyph_name].draw(pen)
        xs += [p[0] + dx for _, operands in pen.value for p in operands]
    return math.floor(min(xs) / GRID) * GRID, math.ceil(max(xs) / GRID) * GRID


def mark_zone_figure(style_key):
    """A tikzpicture for the style."""
    info = FONTS[f"{style_key}_patch"]
    ttfont = TTFont(info["path"])
    glyphset = ttfont.getGlyphSet()
    anchors, _ = extract_mark_attachment_data(ttfont, info["lookup_index"])

    marks = (_placed_marks(ttfont, anchors, MARK_ABOVE, ABOVE)
             + _placed_marks(ttfont, anchors, MARK_BELOW, BELOW))
    x_min, x_max = _x_range(ttfont, glyphset, marks)
    y_min, y_max = Y_RANGE

    lines = [f"\\begin{{tikzpicture}}[x=1pt,y=1pt,scale={SCALE}]"]

    lines.append(f"\\draw[black!12,line width=0.1pt,step={GRID}] "
                 f"({x_min},{y_min}) grid ({x_max},{y_max});")
    for y in range(y_min, y_max + 1, GRID):
        if y % LABEL_EVERY == 0:
            lines.append(f"\\node[left,font=\\tiny,inner sep=1pt] at ({x_min},{y}) {{{y}}};")
    for x in range(x_min, x_max + 1, GRID):
        if x % LABEL_EVERY == 0:
            lines.append(f"\\node[below,font=\\tiny,inner sep=1pt] at ({x},{y_min}) {{{x}}};")

    lines.append(f"\\fill[black!28,even odd rule] {_outline(glyphset, BASE)};")

    common_last = sorted(marks, key=lambda mark: mark[3] in MARK_COMMON)
    for glyph_name, dx, dy, codepoint in common_last:
        command = ("\\draw[black,line width=0.25pt]" if codepoint in MARK_COMMON else
                   "\\filldraw[draw=black!35,line width=0.1pt,fill=black,fill opacity=0.03,"
                   "draw opacity=1,even odd rule]")
        lines.append(f"{command} {_outline(glyphset, glyph_name, dx, dy)};")

    for anchor_class in (ABOVE, BELOW):
        anchor = anchors[BASE][anchor_class]
        lines.append(f"\\fill[blue] ({anchor.XCoordinate},{anchor.YCoordinate}) circle (7);")

    lines.append("\\end{tikzpicture}")
    return "\n".join(lines) + "\n", len(marks)
