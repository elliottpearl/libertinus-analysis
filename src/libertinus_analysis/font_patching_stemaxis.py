# font_patching_stemaxis.py
"""
Stem-axis rule for central-stem letters, stage 7b of the patching pipeline
(after the human-curated anchors, before the derived letters).

A central-stem letter (CENTRAL_STEM: i, ı, j, ȷ, l, m by its middle stem, I,
T, ɪ; the basest letters with a central stem and no curl, never the letters
derived from them, which stage 8 moves with their base letter) has its above
anchor, and all but j and ȷ their below anchor, on the axis of its stem:

    X = m(y_ref) + (Y - y_ref) tan(theta) - K

where m is the midline of the stem (stem_line in font_patching_inherit.py:
the mean of the stem's two straight edges, from the control points), y_ref is
the top of the straight part for the above anchor and its bottom for the
below anchor, theta is the style's slant and K the style's shift for the class
(150 above and -12 below in semibold italic, else 0). Y is not touched.

The stem is taken where it ends and carried to the anchor at the style's
slant, not at the stem's own angle: the italic stems are drawn steeper than
the declared slant (italic i 12.9 degrees, semibold italic i 13.4, against 12
and 11.5), and the mark, whose axis runs at the declared slant, is seen
against the end of the stem. Carried at the stem's own angle, the above
anchor would move 5-8 units right in italic and 11-17 in semibold italic
(decided 2026-11-12).

In the italic styles curls move the optical centre off the stem: dotted i and
j take the centre of the dot (DOT_CENTRED), ı and ȷ the axis of that dot
(DOT_AXIS_OF), and the below anchors of i ı l (CURL_FOOT, the curled foot) and
the above anchor of m (CURL_ABOVE, the arches) are left out, to be curated.

There is no threshold, and the rule overrules every earlier anchor, the
designer's and the curated ones (stage 7) alike, in X; each curated X it
changes is reported. Letters missing from the font, without the anchor, or
whose stem is not found are reported and left.
"""

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

from .fontmetrics_helpers import SHIFT_K, SLOPE
from .font_patching_anchors import load_human_anchors
from .font_patching_inherit import (
    find_mark_to_base_subtables,
    get_anchor_from_baserec,
    get_base_record_for_glyph,
    set_anchor_in_baserec,
    stem_line,
)

# Central-stem letters and the classes (0 above, 2 below) set on the stem's axis.
# j and ȷ below are left out: their below anchor is under the hook, not the stem.
CENTRAL_STEM = {
    0x0069: (0, 2),  # i
    0x0131: (0, 2),  # ı dotless i
    0x006A: (0,),    # j
    0x0237: (0,),    # ȷ dotless j
    0x006C: (0, 2),  # l
    0x006D: (0, 2),  # m: its middle stem (above in the upright styles only, CURL_ABOVE)
    0x0049: (0, 2),  # I
    0x0054: (0, 2),  # T
    0x026A: (0, 2),  # ɪ small capital I
}
# Letters whose stem is found as the one nearest the centre of the glyph, not the tallest.
CENTRAL = (0x006D,)
# Not central-stem letters (2026-11-12, test sheets): ɾ U+027E and ɿ U+027F, whose hooked top puts
# the optical centre 40-55 units off the stem; never letters derived from the basest ones.
CLASS_NAMES = {0: "above", 2: "below"}
ITALIC_STYLES = ("italic", "semibold_italic")
# In the italic styles the above anchor of dotted i and j is centred on the dot, which is
# drawn 11-13 left of the stem's axis: only U+033F attaches there, right over the dot (2026-11-12).
DOT_CENTRED = (0x0069, 0x006A)
# ... and the above anchor of dotless ı and ȷ on the axis of the dot of i and j: the accent takes the
# dot's place. Their curved entry stroke at the top left pulls the optical centre left of the stem;
# the precomposed ì í î … ĵ ǰ put their accents left of it too (2026-11-12).
DOT_AXIS_OF = {0x0131: 0x0069, 0x0237: 0x006A}
# In the italic styles the foot of i, ı and l curls right, and the optical centre under it is
# right of the stem's axis: their below anchors are left out of the rule, for curation (2026-11-12).
CURL_FOOT = (0x0069, 0x0131, 0x006C)
# How the stem's midline is carried from the end of its straight part to the anchor:
# "declared" at the style's slant, "stem" at the stem's own angle (the midline extended).
# "stem" was tested and rejected (2026-11-12): the designer's dots and precomposed accents
# sit left of the line at the declared slant, and the steeper stems would move anchors right.
# In the italic styles the arches of m curl over its middle stem, and the optical centre above is
# off the stem: m above is left out of the rule there, for curation (2026-11-12).
CURL_ABOVE = (0x006D,)
ANGLE = "declared"


def stem_axis_x(ttfont, font_key, glyph_name, anchor_class, y, angle=ANGLE, central=False):
    """The anchor X on the stem's axis at height y, or None if the stem is not found."""
    found = stem_line(ttfont.getGlyphSet(), glyph_name, central=central)
    if found is None:
        return None
    midline, y_bottom, y_top = found
    k = SHIFT_K.get(font_key, {}).get(str(anchor_class), 0)
    if angle == "stem":
        return midline(y) - k
    y_ref = y_top if anchor_class == 0 else y_bottom
    return midline(y_ref) + (y - y_ref) * SLOPE[font_key] - k


def dot_centre_x(ttfont, font_key, glyph_name, y):
    """The above anchor X over the centre of the dot (contours above the stem), at height y, less K."""
    glyphset = ttfont.getGlyphSet()
    slope = SLOPE[font_key]
    _, _, y_top = stem_line(glyphset, glyph_name)
    pen = RecordingPen()
    glyphset[glyph_name].draw(pen)
    boxes, contour = [], []
    for op, args in pen.value:
        contour.append((op, args))
        if op in ("closePath", "endPath"):
            bp = BoundsPen(None)
            tp = TransformPen(bp, (1, 0, -slope, 1, 0, 0))
            for o, a in contour:
                getattr(tp, o)(*a)
            if bp.bounds and bp.bounds[1] > y_top + 100:
                boxes.append(bp.bounds)
            contour = []
    if not boxes:
        return None
    centre = (min(b[0] for b in boxes) + max(b[2] for b in boxes)) / 2
    return centre + y * slope - SHIFT_K.get(font_key, {}).get("0", 0)


def patch_stem_axis(ttfont, font_key, lookup_index):
    """Move the X of each central-stem letter's above/below anchor onto its stem's axis."""
    report = []
    subtables = find_mark_to_base_subtables(ttfont, lookup_index)
    if not subtables:
        return [f"No MarkToBase (LookupType 4) subtables found in lookup {lookup_index}; SKIPPED"]
    sub = subtables[0]
    cmap = ttfont.getBestCmap()
    human = load_human_anchors(font_key)

    for cp, classes in CENTRAL_STEM.items():
        glyph_name = cmap.get(cp)
        if glyph_name is None:
            report.append(f"U+{cp:04X}: not in the font; SKIPPED")
            continue
        for anchor_class in classes:
            name = f"U+{cp:04X} {glyph_name} {CLASS_NAMES[anchor_class]}"
            curated = (human.get("bases", {}).get(cp, {}).get(anchor_class)
                       or human.get("bases_by_name", {}).get(glyph_name, {}).get(anchor_class))
            baserec, _ = get_base_record_for_glyph(sub, glyph_name)
            xy = get_anchor_from_baserec(baserec, anchor_class) if baserec is not None else None
            if xy is None:
                report.append(f"{name}: no anchor; SKIPPED")
                continue
            italic = font_key in ITALIC_STYLES
            if italic and anchor_class == 2 and cp in CURL_FOOT:
                report.append(f"{name}: curl foot, left out of the rule; anchor {xy} kept, for curation")
                continue
            if italic and anchor_class == 0 and cp in CURL_ABOVE:
                report.append(f"{name}: curls over the stem, left out of the rule; anchor {xy} kept, for curation")
                continue
            if italic and anchor_class == 0 and cp in DOT_CENTRED:
                x, where = dot_centre_x(ttfont, font_key, glyph_name, xy[1]), "dot"
            elif italic and anchor_class == 0 and cp in DOT_AXIS_OF:
                dotted = cmap[DOT_AXIS_OF[cp]]
                x, where = dot_centre_x(ttfont, font_key, dotted, xy[1]), f"axis of the dot of {dotted}"
            else:
                x, where = stem_axis_x(ttfont, font_key, glyph_name, anchor_class, xy[1],
                                       central=cp in CENTRAL), "stem's axis"
            if x is None:
                report.append(f"{name}: stem not found; anchor {xy} left; SKIPPED")
                continue
            source = "curated (stage 7)" if curated is not None else "designer or stage 6"
            if round(x) != xy[0]:
                set_anchor_in_baserec(baserec, anchor_class, round(x), xy[1])
                report.append(f"{name}: {source} anchor {xy} -> ({round(x)}, {xy[1]}), "
                              f"on the {where} ({x:.1f})" + ("; CURATED X OVERRULED" if curated else ""))
    return report
