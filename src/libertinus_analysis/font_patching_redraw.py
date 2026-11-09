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

    ʅ (U+0285), all styles  Squat reversed esh, the Sinological apical vowel
                         after retroflex sibilants (ʂʅ, tʂʅ): ɿ with a retroflex
                         hook. The designer's was 550 high in regular and a
                         mirrored ʃ (ascender height) in the other styles; every
                         font that draws it rather than mirroring ʃ tops it at
                         the x-height, level with ɿ (survey, 2026-11-09). Rebuilt
                         as ɿ's fishhook and stem with ɳ's retroflex hook in
                         place of the foot serif: the hook descends as far as
                         ɳ's (about 220-230, short of the descender, like the
                         other retroflex hooks). Left sidebearing ɿ's, right
                         sidebearing ɳ's at the hook.

    ɿ with descender, U+E27F "uni027F.desc", all styles
                         Libertinus's ɿ sits on the baseline; Gentium Plus,
                         Charis SIL, Andika, Noto, Tinos and Roboto descend.
                         This is ɿ's fishhook and stem run down to q's
                         descender serif; advance ɿ's.

The grafts translate the added part (hook or serif) so that its left stem
edge lies on ɿ's left stem edge (in the italics, the sheared edge line), and
move the points of its right half by the few units that put its right stem
edge on ɿ's.

Each rebuild checks the control points it relies on and raises if they are
not where expected, so a change to the source glyphs fails loudly.
"""

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.boundsPen import BoundsPen

from .font_patching_addmarks import _encode, _set_outline


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


# ------------------------------------------------------------
# ʅ and the descending ɿ: grafts onto ɿ
# ------------------------------------------------------------

# ɿ (uni027F): `top` are the segments from the lineTo up the right stem edge,
# round the fishhook, to the last point on the left stem edge; the closePath
# then runs down the left edge. `left` and `right` are two points on each stem
# edge (sheared in the italics).
RHO = {
    "regular": dict(top=slice(11, 19), first=("lineTo", ((257, 215),)), last=(182, 230),
                    left=((182, 230), (182, 73)), right=((257, 73), (257, 215))),
    "italic": dict(top=slice(12, 23), first=("lineTo", ((305, 208),)), last=(234, 224),
                   left=((234, 224), (199, 72)), right=((273, 72), (305, 208))),
    "semibold": dict(top=slice(11, 19), first=("lineTo", ((290, 216),)), last=(172, 232),
                     left=((172, 232), (172, 76)), right=((290, 76), (290, 216))),
    "semibold_italic": dict(top=slice(12, 23), first=("lineTo", ((340, 216),)), last=(226, 232),
                            left=((226, 232), (190, 76)), right=((308, 76), (340, 216))),
}

# ɳ (uni0273): the retroflex hook, from `start` on the left edge of the right
# stem, down round the hook, up to `end` on its right edge.
HOOK = {
    "regular": dict(segs=[slice(1, 9)], start=(364, 109), end=(439, 75)),
    "italic": dict(segs=[slice(27, 31), slice(1, 6)], start=(329, 31), end=(446, 184)),
    "semibold": dict(segs=[slice(28, 36)], start=(351, 4), end=(468, 4)),
    "semibold_italic": dict(segs=[slice(30, 40)], start=(352, 4), end=(469, 4)),
}

# q: the descender serif, from `start` on the stem's left edge round to `end`
# on its right edge (q's serif is symmetric about its stem).
SERIF = {
    "regular": dict(segs=[slice(1, 7)], start=(346, -111), end=(425, -111)),
    "italic": dict(segs=[slice(1, 13)], start=(295, -161), end=(371, -161)),
    "semibold": dict(segs=[slice(1, 13)], start=(335, -155), end=(445, -155)),
    "semibold_italic": dict(segs=[slice(1, 8)], start=(309, -110), end=(427, -107)),
}

DESC_RHO_CODEPOINT = 0xE27F
DESC_RHO_NAME = "uni027F.desc"


def _edge_x(edge, y):
    (x0, y0), (x1, y1) = edge
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def _end(segment):
    return segment[1][-1]


def _piece(recording, spec, glyph_label):
    """The segments of an added part, after checking its end points."""
    segs = [s for part in spec["segs"] for s in recording[part]]
    before = recording[spec["segs"][0].start - 1]
    if _end(before) != spec["start"] or _end(segs[-1]) != spec["end"]:
        raise ValueError(f"{glyph_label} is not as expected: {before} ... {segs[-1]}")
    return segs


def _graft(rho, rho_spec, segs, start, end):
    """
    ɿ's top with an added part (hook or serif) in place of its foot. Returns
    the outline (one contour).
    """
    top = rho[rho_spec["top"]]
    if top[0] != rho_spec["first"] or _end(top[-1]) != rho_spec["last"]:
        raise ValueError(f"ɿ is not as expected: {top[0]} ... {top[-1]}")

    dx = _edge_x(rho_spec["left"], start[1]) - start[0]
    extra = _edge_x(rho_spec["right"], end[1]) - (end[0] + dx)
    middle = (start[0] + end[0]) / 2

    def moved(point):
        x, y = point
        return (round(x + dx + (extra if x > middle else 0)), y)

    grafted = [(op, tuple(moved(p) for p in pts)) for op, pts in segs]
    return [("moveTo", (moved(start),))] + grafted + list(top) + [("closePath", ())]


def _bounds(recording):
    pen = BoundsPen(None)
    for operator, operands in recording:
        getattr(pen, operator)(*operands)
    return pen.bounds


def _squat_reversed_esh(glyphset, font_key):
    """ʅ: ɿ's top with ɳ's retroflex hook. Returns (outline, advance)."""
    rho = _recording(glyphset, "uni027F")
    eng = _recording(glyphset, "uni0273")
    spec = HOOK[font_key]
    hook = _piece(eng, spec, "ɳ")
    outline = _graft(rho, RHO[font_key], hook, spec["start"], spec["end"])
    # Right sidebearing ɳ's, measured at the hook (semibold italic ɳ is widest at its top serif)
    eng_rsb = glyphset["uni0273"].width - _bounds([("moveTo", (spec["start"],))] + hook)[2]
    return outline, round(_bounds(outline)[2] + eng_rsb)


def _descending_rho(glyphset, font_key):
    """ɿ with a descender: ɿ's top with q's descender serif. Returns (outline, advance)."""
    rho = _recording(glyphset, "uni027F")
    q = _recording(glyphset, "q")
    spec = SERIF[font_key]
    outline = _graft(rho, RHO[font_key], _piece(q, spec, "q"), spec["start"], spec["end"])
    return outline, glyphset["uni027F"].width


def _add_base_glyph(ttfont, glyph_name, codepoint, outline, advance):
    _set_outline(ttfont, glyph_name, outline)   # creates the glyph (GDEF mark, zero advance)
    _replace_outline(ttfont, glyph_name, outline, advance)
    ttfont["GDEF"].table.GlyphClassDef.classDefs[glyph_name] = 1   # base
    _encode(ttfont, codepoint, glyph_name)


def redraw_glyphs(ttfont, font_key):
    """Apply the outline fixes for this style. Returns report lines."""
    report = []
    glyphset = ttfont.getGlyphSet()
    if font_key == "semibold":
        outline, advance = _semibold_retroflex_l(glyphset)
        old = ttfont["hmtx"]["uni026D"][0]
        _replace_outline(ttfont, "uni026D", outline, advance)
        report.append(f"uni026D: rebuilt from l and the hook of uni0256; advance {old} -> {advance}")

    if font_key in RHO:
        # Both from the original ɿ, ɳ and q, read before either glyph changes
        esh, esh_advance = _squat_reversed_esh(glyphset, font_key)
        rho, rho_advance = _descending_rho(glyphset, font_key)

        old = ttfont["hmtx"]["uni0285"][0]
        _replace_outline(ttfont, "uni0285", esh, esh_advance)
        report.append(f"uni0285: rebuilt from uni027F and the hook of uni0273; "
                      f"bbox {tuple(round(v) for v in _bounds(esh))}, advance {old} -> {esh_advance}")

        if DESC_RHO_NAME not in ttfont.getGlyphOrder():
            _add_base_glyph(ttfont, DESC_RHO_NAME, DESC_RHO_CODEPOINT, rho, rho_advance)
            report.append(f"{DESC_RHO_NAME} U+{DESC_RHO_CODEPOINT:04X}: added from uni027F and the "
                          f"descender serif of q; bbox {tuple(round(v) for v in _bounds(rho))}, "
                          f"advance {rho_advance}")
    return report
