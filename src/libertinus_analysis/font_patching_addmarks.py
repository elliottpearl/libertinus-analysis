# font_patching_addmarks.py
"""
Add the combining marks that a style lacks, with their mark anchors.

Part of the glyph-creation stage (see font_patching_addglyphs.py). Nothing
is drawn from scratch: every new mark is an outline that the designer drew
in another style or in a precomposed glyph, moved by the transformation that
the designer's own marks follow between those styles.

    semibold         regular's outline; moved right by 12 units if it is an
                     above mark, as semibold's own above marks are. The
                     anchor is regular's, moved with the outline.

    semibold italic  italic's outline, moved right by 12 units, as semibold
                     italic's own marks are. (Italic's marks are regular's,
                     sheared by x' = x + 0.2035 y.) The anchor is regular's
                     anchor verbatim: this is the semibold italic anchor
                     model, see the report.

    dot above right  (U+0358) the style's own combining dot above, moved to
                     where the source style has its dot.

    dotaccent.cap    (italic, semibold italic) the dot of the precomposed
                     Idotaccent, at the height it has in the precomposed
                     dotted capitals, with its anchor at the capital
                     reference height.

The designer does not thicken below marks between weights, but thickens
above marks by about 12 percent. So a copied above mark is made bolder:

    - a part that is another mark (the grave tone mark is the grave, the
      bridge above is the bridge below, the fermata contains the inverted
      breve, ...) is replaced by the style's own, already bold, mark;
    - the rest of the outline is pushed outward (embolden()).

Lines, combining letters and dots are left as copied: the designer's lines
and modifier letters are not thickened, and the dot is the style's own.

Double marks (U+035C-U+0361) have no anchors in regular and get none here.
In semibold, U+0358-U+0363 are copies of the capital accents (U+0358 is
grave.cap, and so on); their outlines and anchors are replaced.

Not added: the stretchy variants of the low line and overline
(uni0332.100 etc.), U+0344, U+0345 and U+0483.
"""

import math

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otTables import Anchor, GlyphClassDef, MarkRecord

from .font_context import FONTS

# Style whose outlines are copied, and the style whose anchors are used.
OUTLINE_SOURCE = {"semibold": "regular", "semibold_italic": "italic"}
ANCHOR_SOURCE = "regular"

# Anchor classes of regular's mark-to-base lookup.
ABOVE, BELOW = 0, 2

# Horizontal shift of the copied outline (see the module docstring).
SHIFT = 12

# Marks to add where missing: low lines, overlays, the rest of the below and
# above marks, the double marks and the combining letters.
MARKS = (
    list(range(0x0332, 0x0338))
    + list(range(0x0339, 0x0342))
    + list(range(0x0346, 0x034F))
    + list(range(0x0350, 0x0370))
)

# Glyphs that exist in the style but hold the wrong outline.
REPLACE = {
    "semibold": set(range(0x0358, 0x0364)),
}

# Above marks are made bolder, except lines and combining letters.
NOT_EMBOLDENED = {0x033F} | set(range(0x0363, 0x0370))
# Marks that may be part of another mark; the style's own is used instead.
COMPONENTS = ("gravecomb", "acutecomb", "tildecomb", "uni0311", "uni032A", "uni0306")
# Outward push per side, as a fraction of the mean stroke thickness. This
# thickens a stroke by about 12 percent, as the designer's above marks are.
EMBOLDEN = 0.075

# Marks whose outline is the style's own dot (uni0307), not the source's.
DOT_MARKS = {0x0358}
DOT_GLYPH = "uni0307"

# dotaccent.cap: taken from the precomposed dotted capitals.
CAP_DOT_STYLES = {"italic", "semibold_italic"}
CAP_DOT_NAME = "dotaccent.cap"
CAP_DOT_SOURCE = 0x0130       # Idotaccent; its topmost contour is the dot
CAP_DOT_CENTRE_Y = 750        # median height of that dot over A-Z, all styles
CAP_ANCHOR_Y = 850            # above-anchor reference of capitals
SLOPE = {
    "italic": math.tan(math.radians(12)),
    "semibold_italic": math.tan(math.radians(11.5)),
}
# Semibold italic anchor model: anchors are left of the axis by this shift.
SEMIBOLD_ITALIC_K = 150


# ------------------------------------------------------------
# Outlines
# ------------------------------------------------------------

def _recording(glyphset, glyph_name):
    pen = RecordingPen()
    glyphset[glyph_name].draw(pen)
    return pen.value


def _replay(recording, pen):
    for operator, operands in recording:
        getattr(pen, operator)(*operands)


def _bounds(recording):
    pen = BoundsPen(None)
    _replay(recording, pen)
    return pen.bounds


def _contours(recording):
    """Split a recording into one recording per contour."""
    contours, current = [], []
    for step in recording:
        current.append(step)
        if step[0] in ("closePath", "endPath"):
            contours.append(current)
            current = []
    return contours


def _centre(recording):
    x0, y0, x1, y1 = _bounds(recording)
    return (x0 + x1) / 2, (y0 + y1) / 2


def _translated(recording, dx, dy):
    return [
        (operator, tuple((x + dx, y + dy) for x, y in operands))
        for operator, operands in recording
    ]


def _points(contour):
    return [point for _, operands in contour for point in operands]


def _find_component(contours, component):
    """
    Indices of the contours that are `component` (a list of contours) under
    one translation, or None.
    """
    if not component:
        return None
    first = _points(component[0])
    for candidate in contours:
        points = _points(candidate)
        if len(points) != len(first):
            continue
        tx, ty = points[0][0] - first[0][0], points[0][1] - first[0][1]
        used = []
        for part in component:
            part_points = _points(part)
            for index, other in enumerate(contours):
                other_points = _points(other)
                if index in used or len(other_points) != len(part_points):
                    continue
                if all(abs(b[0] - a[0] - tx) <= 1.01 and abs(b[1] - a[1] - ty) <= 1.01
                       for a, b in zip(part_points, other_points)):
                    used.append(index)
                    break
            else:
                break
        else:
            return used
    return None


# ------------------------------------------------------------
# Emboldening
# ------------------------------------------------------------

def _unit(dx, dy):
    length = math.hypot(dx, dy)
    return (dx / length, dy / length) if length else (0.0, 0.0)


def _segments(recording):
    """Closed contours as lists of segments: (p0, p1) or (p0, c1, c2, p3)."""
    contours, segments, start, current = [], [], None, None
    for operator, points in recording:
        if operator == "moveTo":
            start = current = points[0]
            segments = []
        elif operator == "lineTo":
            if points[0] != current:
                segments.append((current, points[0]))
            current = points[0]
        elif operator == "curveTo":
            segments.append((current, points[0], points[1], points[2]))
            current = points[2]
        elif operator in ("closePath", "endPath"):
            if current != start:
                segments.append((current, start))
            if segments:
                contours.append(segments)
            segments = []
    return contours


def _flat(segments, steps=8):
    """Polygon approximating a contour."""
    polygon = []
    for segment in segments:
        if len(segment) == 2:
            polygon.append(segment[0])
            continue
        p0, c1, c2, p3 = segment
        for step in range(steps):
            t = step / steps
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            polygon.append((
                a * p0[0] + b * c1[0] + c * c2[0] + d * p3[0],
                a * p0[1] + b * c1[1] + c * c2[1] + d * p3[1],
            ))
    return polygon


def _area(polygon):
    return sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1])
    ) / 2


def stroke_thickness(recording):
    """Mean stroke thickness of an outline: twice its area over its perimeter."""
    area = perimeter = 0.0
    for segments in _segments(recording):
        polygon = _flat(segments)
        area += _area(polygon)
        perimeter += sum(
            math.hypot(x1 - x0, y1 - y0)
            for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1])
        )
    return 2 * abs(area) / perimeter if perimeter else 0.0


def embolden(recording, distance, miter_limit=3.0):
    """
    Push an outline outward by `distance` units.

    Each node moves along the mitre of the normals of its two segments, and
    a control point moves with its node. Good for a few units on simple
    shapes; it is not a general outline offset.
    """
    contours = _segments(recording)
    if not contours:
        return recording
    # In the largest contour, find which side of the direction of travel is outside.
    outer = max(contours, key=lambda segments: abs(_area(_flat(segments))))
    sign = 1.0 if _area(_flat(outer)) > 0 else -1.0

    def tangent_out(segment):
        for point in segment[1:]:
            if point != segment[0]:
                return _unit(point[0] - segment[0][0], point[1] - segment[0][1])
        return (0.0, 0.0)

    def tangent_in(segment):
        for point in reversed(segment[:-1]):
            if point != segment[-1]:
                return _unit(segment[-1][0] - point[0], segment[-1][1] - point[1])
        return (0.0, 0.0)

    def moved(point, shift):
        return (point[0] + shift[0], point[1] + shift[1])

    result = []
    for segments in contours:
        count = len(segments)
        shifts = []                      # shift of the start node of each segment
        for index in range(count):
            t_in = tangent_in(segments[index - 1])
            t_out = tangent_out(segments[index])
            n_in = (t_in[1] * sign, -t_in[0] * sign)
            n_out = (t_out[1] * sign, -t_out[0] * sign)
            cosine = n_in[0] * n_out[0] + n_in[1] * n_out[1]
            scale = distance / max(1.0 + cosine, 2.0 / miter_limit)
            shifts.append(((n_in[0] + n_out[0]) * scale, (n_in[1] + n_out[1]) * scale))

        result.append(("moveTo", (moved(segments[0][0], shifts[0]),)))
        for index, segment in enumerate(segments):
            here, there = shifts[index], shifts[(index + 1) % count]
            if len(segment) == 4:
                result.append(("curveTo", (
                    moved(segment[1], here), moved(segment[2], there), moved(segment[3], there),
                )))
            elif index < count - 1:
                result.append(("lineTo", (moved(segment[1], there),)))
        result.append(("closePath", ()))
    return result


def _bolder(outline, source_glyphs, glyphset):
    """
    Make a copied above mark as bold as the style's own above marks.
    `outline` is the source style's outline (not yet shifted).

    Returns (new outline, name of the component if the whole mark is that
    glyph in place else None, description).
    """
    contours = _contours(outline)
    parts, notes = [], []
    for name in COMPONENTS:
        if name not in source_glyphs or name not in glyphset:
            continue
        component = _contours(_recording(source_glyphs, name))
        found = _find_component(contours, component)
        if not found:
            continue
        matched = [step for index in found for step in contours[index]]
        own = _recording(glyphset, name)
        in_place = _centre(matched) == _centre(_recording(source_glyphs, name))
        if in_place and len(found) == len(contours):
            return own, name, f"is the style's own {name}"
        cx, cy = _centre(matched)
        own_cx, own_cy = _centre(own)
        parts.append(_translated(own, cx - own_cx, cy - own_cy))
        contours = [c for index, c in enumerate(contours) if index not in found]
        notes.append(f"own {name}")

    rest = [step for contour in contours for step in contour]
    if rest:
        distance = EMBOLDEN * stroke_thickness(rest)
        parts.append(embolden(rest, distance))
        notes.append(f"emboldened by {distance:.1f}")
    return [step for part in parts for step in part], None, ", ".join(notes)


def _set_outline(ttfont, glyph_name, recording, dx=0, dy=0):
    """
    Give glyph_name (zero advance width) the recorded outline moved by
    (dx, dy), creating the glyph if needed.
    """
    top = ttfont["CFF "].cff.topDictIndex[0]
    charstrings = top.CharStrings
    private = top.Private

    # A zero advance width is the default width, so it is omitted.
    width = None if private.defaultWidthX == 0 else 0 - private.nominalWidthX
    pen = T2CharStringPen(width, None)
    _replay(recording, TransformPen(pen, (1, 0, 0, 1, dx, dy)))
    charstring = pen.getCharString(private=private, globalSubrs=top.GlobalSubrs)

    if glyph_name in charstrings.charStrings:
        charstrings[glyph_name] = charstring
    else:
        glyph_order = ttfont.getGlyphOrder()
        glyph_order.append(glyph_name)
        ttfont.setGlyphOrder(glyph_order)
        if top.charset is not glyph_order and glyph_name not in top.charset:
            top.charset.append(glyph_name)
        charstrings.charStrings[glyph_name] = len(charstrings.charStringsIndex)
        charstrings.charStringsIndex.append(charstring)

    bounds = _bounds(recording)
    lsb = round(bounds[0] + dx) if bounds else 0
    ttfont["hmtx"].metrics[glyph_name] = (0, lsb)

    gdef = ttfont["GDEF"].table
    if gdef.GlyphClassDef is None:
        gdef.GlyphClassDef = GlyphClassDef()
        gdef.GlyphClassDef.classDefs = {}
    gdef.GlyphClassDef.classDefs[glyph_name] = 3   # mark


def _encode(ttfont, codepoint, glyph_name):
    for table in ttfont["cmap"].tables:
        if table.isUnicode():
            table.cmap[codepoint] = glyph_name


# ------------------------------------------------------------
# Mark anchors
# ------------------------------------------------------------

def _mark_subtables(ttfont, lookup_index):
    lookup = ttfont["GPOS"].table.LookupList.Lookup[lookup_index]
    return [sub for sub in lookup.SubTable if sub.LookupType == 4]


def _mark_anchor(ttfont, lookup_index, glyph_name):
    """(class, (x, y)) of a mark in the mark-to-base lookup, or None."""
    for sub in _mark_subtables(ttfont, lookup_index):
        glyphs = sub.MarkCoverage.glyphs
        if glyph_name in glyphs:
            record = sub.MarkArray.MarkRecord[glyphs.index(glyph_name)]
            anchor = record.MarkAnchor
            return record.Class, (anchor.XCoordinate, anchor.YCoordinate)
    return None


def _set_mark_anchor(ttfont, lookup_index, glyph_name, mark_class, xy):
    """Set or create the mark record, keeping the coverage in glyph-ID order."""
    for sub in _mark_subtables(ttfont, lookup_index):
        if mark_class >= sub.ClassCount:
            continue
        glyphs = sub.MarkCoverage.glyphs
        records = sub.MarkArray.MarkRecord
        if glyph_name in glyphs:
            record = records[glyphs.index(glyph_name)]
        else:
            record = MarkRecord()
            record.MarkAnchor = Anchor()
            record.MarkAnchor.Format = 1
            glyph_id = ttfont.getGlyphID(glyph_name)
            index = len(glyphs)
            for i, other in enumerate(glyphs):
                if ttfont.getGlyphID(other) > glyph_id:
                    index = i
                    break
            glyphs.insert(index, glyph_name)
            records.insert(index, record)
        record.Class = mark_class
        record.MarkAnchor.XCoordinate = round(xy[0])
        record.MarkAnchor.YCoordinate = round(xy[1])
        return True
    return False


def _remove_mark_anchor(ttfont, lookup_index, glyph_name):
    for sub in _mark_subtables(ttfont, lookup_index):
        glyphs = sub.MarkCoverage.glyphs
        if glyph_name in glyphs:
            index = glyphs.index(glyph_name)
            del glyphs[index]
            del sub.MarkArray.MarkRecord[index]


# ------------------------------------------------------------
# Stages
# ------------------------------------------------------------

def add_missing_marks(ttfont, font_key):
    """Add the marks of MARKS that font_key lacks. Returns a report."""
    if font_key not in OUTLINE_SOURCE:
        return []

    source_key = OUTLINE_SOURCE[font_key]
    source = TTFont(FONTS[source_key]["path"])
    source_glyphs = source.getGlyphSet()
    source_cmap = source.getBestCmap()
    anchors = TTFont(FONTS[ANCHOR_SOURCE]["path"])
    anchors_cmap = anchors.getBestCmap()
    anchors_lookup = FONTS[ANCHOR_SOURCE]["lookup_index"]

    lookup_index = FONTS[font_key]["lookup_index"]
    glyphset = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()
    italic = font_key == "semibold_italic"
    dot = _recording(glyphset, DOT_GLYPH)

    report = []
    for codepoint in MARKS:
        if codepoint not in source_cmap or codepoint not in anchors_cmap:
            continue
        glyph_name = cmap.get(codepoint)
        if glyph_name is not None:
            has_outline = bool(_recording(glyphset, glyph_name))
            if has_outline and codepoint not in REPLACE.get(font_key, ()):
                continue
            action = "replaced" if has_outline else "filled"
        else:
            glyph_name = f"uni{codepoint:04X}"
            action = "added"

        outline = _recording(source_glyphs, source_cmap[codepoint])
        anchor = _mark_anchor(anchors, anchors_lookup, anchors_cmap[codepoint])

        # Shift of the outline, and of the anchor that goes with it.
        if anchor is None:
            dx = anchor_dx = 0                  # double marks stay where they are
        elif italic:
            dx, anchor_dx = SHIFT, None         # anchor is regular's, verbatim
        else:
            dx = anchor_dx = SHIFT if anchor[0] == ABOVE else 0

        note = "copied"
        if (anchor is not None and anchor[0] == ABOVE
                and codepoint not in NOT_EMBOLDENED and codepoint not in DOT_MARKS):
            outline, own_glyph, note = _bolder(outline, source_glyphs, glyphset)
            if own_glyph is not None:
                # The style's own mark, where it is, with its own anchor.
                dx = anchor_dx = 0
                anchor = _mark_anchor(ttfont, lookup_index, own_glyph) or anchor

        if codepoint in DOT_MARKS:
            cx, cy = _centre(outline)
            dot_cx, dot_cy = _centre(dot)
            _set_outline(ttfont, glyph_name, dot, cx + dx - dot_cx, cy - dot_cy)
        else:
            _set_outline(ttfont, glyph_name, outline, dx, 0)
        if action == "added":
            _encode(ttfont, codepoint, glyph_name)

        # Anchor. Semibold italic numbers its classes as regular does;
        # semibold shares only above and below with regular.
        placed = False
        if anchor is not None and (italic or anchor[0] in (ABOVE, BELOW)):
            mark_class, (x, y) = anchor
            placed = _set_mark_anchor(
                ttfont, lookup_index, glyph_name, mark_class, (x + (anchor_dx or 0), y)
            )
        if not placed:
            _remove_mark_anchor(ttfont, lookup_index, glyph_name)

        where = _mark_anchor(ttfont, lookup_index, glyph_name)
        report.append(f"U+{codepoint:04X} {glyph_name} {action} ({note}); anchor {where}")

    return report


def add_cap_dot(ttfont, font_key):
    """Add dotaccent.cap to the italic styles. Returns a report."""
    if font_key not in CAP_DOT_STYLES or CAP_DOT_NAME in ttfont.getGlyphOrder():
        return []

    slope = SLOPE[font_key]
    glyphset = ttfont.getGlyphSet()
    cmap = ttfont.getBestCmap()

    # The dot of the precomposed glyph is its topmost contour.
    contours = _contours(_recording(glyphset, cmap[CAP_DOT_SOURCE]))
    dot = max(contours, key=lambda contour: _bounds(contour)[1])
    cx, cy = _centre(dot)

    # Keep the combining dot above on its own axis: the new dot is the same
    # distance left of the origin, measured along the italic slope.
    ux, uy = _centre(_recording(glyphset, DOT_GLYPH))
    axis = ux - slope * uy                       # where the axis meets the baseline
    target_x = axis + slope * CAP_DOT_CENTRE_Y
    _set_outline(ttfont, CAP_DOT_NAME, dot, target_x - cx, CAP_DOT_CENTRE_Y - cy)

    # Anchor on the axis at the capital reference height, so that the dot
    # keeps its drawn height over a capital; semibold italic anchors are
    # left of the axis by K.
    anchor_x = axis + slope * CAP_ANCHOR_Y
    if font_key == "semibold_italic":
        anchor_x -= SEMIBOLD_ITALIC_K
    lookup_index = FONTS[font_key]["lookup_index"]
    _set_mark_anchor(ttfont, lookup_index, CAP_DOT_NAME, ABOVE, (anchor_x, CAP_ANCHOR_Y))

    where = _mark_anchor(ttfont, lookup_index, CAP_DOT_NAME)
    return [f"{CAP_DOT_NAME} added; anchor {where}"]
