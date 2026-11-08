# font_patching_redraw.py
"""
Outline fixes, part of the glyph stage (stage 2) of the patching pipeline.

Runs before every anchor stage, so that the anchors are computed on the
corrected outlines.

    semibold ɭ (U+026D)  The designer's glyph has a regular-weight stem (75
                         units; semibold l has 110), a plain slab head and a
                         hook deeper than ɖ's. It is rebuilt by control points,
                         the way regular ɭ is built: regular ɭ is regular l
                         with the foot serif replaced by the retroflex hook of
                         regular ɖ (to about 5 units). So semibold ɭ is
                         semibold l with its foot serif replaced by the hook of
                         semibold ɖ, moved onto l's stem (2026-11-08).

Each rebuild checks the control points it relies on and raises if they are
not where expected, so a change to the source glyphs fails loudly.
"""

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.boundsPen import BoundsPen


def _recording(glyphset, glyph_name):
    pen = RecordingPen()
    glyphset[glyph_name].draw(pen)
    return pen.value


def _replace_outline(ttfont, glyph_name, recording, advance):
    """Replace a base glyph's CFF outline and its advance width."""
    top = ttfont["CFF "].cff.topDictIndex[0]
    private = top.Private
    width = None if advance == private.defaultWidthX else advance - private.nominalWidthX
    pen = T2CharStringPen(width, None)
    for operator, operands in recording:
        getattr(pen, operator)(*operands)
    top.CharStrings[glyph_name] = pen.getCharString(private=private, globalSubrs=top.GlobalSubrs)

    bounds = BoundsPen(None)
    for operator, operands in recording:
        getattr(bounds, operator)(*operands)
    ttfont["hmtx"].metrics[glyph_name] = (advance, round(bounds.bounds[0]))


# ------------------------------------------------------------
# Semibold ɭ
# ------------------------------------------------------------

# Semibold l: 0 moveTo (95, 563) down the left stem; 1 lineTo (95, 77);
# 2-13 the foot serif; 14 lineTo (205, 583) up the right stem; 15- the head.
L_START = ("moveTo", ((95, 563),))
L_FOOT_TOP = ("lineTo", ((95, 77),))
L_RIGHT_STEM = ("lineTo", ((205, 583),))
L_STEM = (95, 205)

# Semibold ɖ: segments 9-14 are the hook, from (332, 9) on the stem's left edge
# (x 331) round to (448, 31) on its right edge (x 448).
D_HOOK = slice(9, 15)
D_HOOK_FIRST_END = (480, -186)
D_HOOK_LAST_END = (448, 31)
D_STEM = (331, 448)

# Where the left stem meets the hook, as regular ɭ (94, 36).
HOOK_TOP = 36
# Regular ɭ's advance is its stem's right edge plus 76; scaled by semibold l's
# right sidebearing over regular l's (84 / 90), about 70: advance 275.
RIGHT_SIDE = 70


def _semibold_retroflex_l(glyphset):
    l = _recording(glyphset, "l")
    d = _recording(glyphset, "uni0256")
    if l[0] != L_START or l[1] != L_FOOT_TOP or l[14] != L_RIGHT_STEM:
        raise ValueError(f"semibold l is not as expected: {l[:2]} ... {l[14]}")
    hook = d[D_HOOK]
    if hook[0][1][-1] != D_HOOK_FIRST_END or hook[-1][1][-1] != D_HOOK_LAST_END:
        raise ValueError(f"semibold ɖ's hook is not as expected: {hook[0]} ... {hook[-1]}")

    dx = L_STEM[0] - D_STEM[0]                                   # -236
    narrow = (D_STEM[1] - D_STEM[0]) - (L_STEM[1] - L_STEM[0])   # 117 - 110 = 7
    moved = [(op, tuple((x + dx, y) for x, y in pts)) for op, pts in hook]
    # The first control point on the stem line, as in regular ɭ (94, -141).
    op, pts = moved[0]
    moved[0] = (op, ((L_STEM[0], pts[0][1]),) + pts[1:])
    # The return curve rejoins l's right stem.
    op, pts = moved[-1]
    moved[-1] = (op, tuple((x - narrow, y) for x, y in pts))

    outline = [l[0], ("lineTo", ((L_STEM[0], HOOK_TOP),))] + moved + l[14:]
    return outline, L_STEM[1] + RIGHT_SIDE


def redraw_glyphs(ttfont, font_key):
    """Apply the outline fixes for this style. Returns report lines."""
    report = []
    if font_key == "semibold":
        glyphset = ttfont.getGlyphSet()
        outline, advance = _semibold_retroflex_l(glyphset)
        old = ttfont["hmtx"]["uni026D"][0]
        _replace_outline(ttfont, "uni026D", outline, advance)
        report.append(f"uni026D: rebuilt from l and the hook of uni0256; advance {old} -> {advance}")
    return report
