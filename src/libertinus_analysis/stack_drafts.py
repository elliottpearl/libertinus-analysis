"""
Draft: stacked above marks (2026-11-18). Not part of the patch.

A user types a letter and two above marks in a chosen order. HarfBuzz composes
the letter and the first mark where a precomposed letter exists (a + U+0308 ->
ä), so the second mark attaches to a precomposed letter, by mark-to-base; with
CGJ after the letter, or a letter with no precomposed form (ŋ̈̀, ɛ̃́), the first
mark stays a glyph and the second needs mark-to-mark. (Where the whole triplet
has a precomposed form, u + ̈ + ̀ -> ǜ, normalization takes the designer's glyph.)

Each draft font is the patched font plus, for the ten common above marks
(MARKS, as first and as second mark, with their .cap forms):
- a mark-to-mark lookup (the `mkmk` feature's only lookup; the fonts' few
  existing mkmk lookups are dropped from the feature): each first mark gets a
  stack anchor at its ink top, on its own axis (its mark-to-base anchor's X,
  carried along the declared slant to that height);
- a mark-to-base lookup applied after the main one (added last to `mark`), for
  the precomposed Latin letters that carry exactly one above mark, from
  MARKS: a stack anchor at the glyph's ink top, centred on the mark's ink,
  along the slant; it overrides the designer's stacking anchors (regular ä ö ü)
  so that both paths agree.
The second mark's anchor in both lookups sets the gap, ink to ink, between the
first mark's top and the second mark's bottom:
- "U" (uniform): one gap per style, UNIFORM_K x the median, over the ten
  marks, of each mark's gap over x-height letters in the patched font;
- "P" (proportional): each mark PROPORTIONAL_K x its own gap over x-height
  letters (over H for a .cap form).
Gap of a mark over a base = base anchor Y + (mark ink bottom - mark anchor Y)
- base ink top (o for x-height marks, H for .cap marks).
"""
import math
import statistics
import unicodedata as ud

from fontTools.otlLib.builder import buildMarkBasePosSubtable
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

from .font_context import FONTS
from .font_naming import save_renamed

MARKS = (0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0306, 0x0307, 0x0308, 0x030A, 0x030C)
UNIFORM_K = 0.5
PROPORTIONAL_K = 0.5
VARIANTS = ("U", "P")
SLANT = {"regular": 0.0, "semibold": 0.0,
         "italic": math.tan(math.radians(11.5)), "semibold_italic": math.tan(math.radians(11.5))}
FILE = {"regular": "Regular", "italic": "Italic", "semibold": "Semibold", "semibold_italic": "SemiboldItalic"}
# letters whose "above" mark is drawn beside the letter or below it
NOT_STACKABLE = set("ďľťĎĽŤģĢķļņŗ")


def _bounds(gs, name):
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return bp.bounds


def _contour_bounds(gs, name):
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    out, cur = [], []
    for op, args in pen.value:
        cur.append((op, args))
        if op == "closePath":
            bp = BoundsPen(gs)
            for o, a in cur:
                getattr(bp, o)(*a)
            out.append(bp.bounds)
            cur = []
    return out


def _full(cp):
    d = ud.decomposition(chr(cp)).split()
    if not d or d[0].startswith("<"):
        return [cp]
    return [c for h in d for c in _full(int(h, 16))]


def _main_lookup(tt, key):
    st = tt["GPOS"].table.LookupList.Lookup[FONTS[key]["lookup_index"]].SubTable[0]
    return getattr(st, "ExtSubTable", st)


def _mark_anchor(st, name):
    gl = st.MarkCoverage.glyphs
    if name not in gl:
        return None
    r = st.MarkArray.MarkRecord[gl.index(name)]
    return r.Class, r.MarkAnchor.XCoordinate, r.MarkAnchor.YCoordinate


def _base_anchor(st, name, cls=0):
    gl = st.BaseCoverage.glyphs
    if name not in gl:
        return None
    a = st.BaseArray.BaseRecord[gl.index(name)].BaseAnchor[cls]
    return a and (a.XCoordinate, a.YCoordinate)


def cap_forms(tt):
    """{mark glyph: its .cap glyph} from the ccmp single substitutions."""
    out = {}
    for lk in tt["GSUB"].table.LookupList.Lookup:
        if lk.LookupType != 1:
            continue
        for st in lk.SubTable:
            st = getattr(st, "ExtSubTable", st)
            out.update({k: v for k, v in st.mapping.items() if v.endswith(".cap")})
    return out


def mark_glyphs(tt):
    """[(codepoint, glyph, is_cap)] for MARKS and their .cap forms."""
    cmap, caps = tt.getBestCmap(), cap_forms(tt)
    out = []
    for cp in MARKS:
        g = cmap[cp]
        out.append((cp, g, False))
        if g in caps:
            out.append((cp, caps[g], True))
    return out


def gaps(tt, key):
    """{glyph: gap over o (or H for .cap forms)} with the patched anchors."""
    gs, cmap, st = tt.getGlyphSet(), tt.getBestCmap(), _main_lookup(tt, key)
    out = {}
    for _, g, cap in mark_glyphs(tt):
        base = cmap[ord("H" if cap else "o")]
        cls, mx, my = _mark_anchor(st, g)
        bx, by = _base_anchor(st, base, cls)
        out[g] = by + (_bounds(gs, g)[1] - my) - _bounds(gs, base)[3]
    return out


def targets(tt, key, variant):
    """{glyph: stacked gap (ink to ink) for that second mark}."""
    g = gaps(tt, key)
    if variant == "U":
        u = UNIFORM_K * statistics.median(g[tt.getBestCmap()[cp]] for cp in MARKS)
        return {k: u for k in g}
    return {k: PROPORTIONAL_K * v for k, v in g.items()}


def stack_bases(tt):
    """{precomposed glyph: (x, y) stack anchor} for the letters with one above mark from MARKS."""
    gs, cmap = tt.getGlyphSet(), tt.getBestCmap()
    out = {}
    for cp, name in cmap.items():
        if not (0xC0 <= cp <= 0x24F or 0x1E00 <= cp <= 0x1EFF) or chr(cp) in NOT_STACKABLE:
            continue
        if not ud.category(chr(cp)).startswith("L"):
            continue
        parts = _full(cp)
        above = [c for c in parts if ud.combining(chr(c)) == 230]
        if len(above) != 1 or above[0] not in MARKS or parts[0] not in cmap or len(parts) != 2:
            continue
        base = parts[0]
        base_glyph = cmap[{0x69: 0x131, 0x6A: 0x237}.get(base, base)]
        btop = _bounds(gs, base_glyph)[3]
        ink = [b for b in _contour_bounds(gs, name) if b[1] >= btop - 10]
        if not ink:
            continue     # the mark is merged with the letter (no separate contour)
        x0, y0 = min(b[0] for b in ink), min(b[1] for b in ink)
        x1, y1 = max(b[2] for b in ink), max(b[3] for b in ink)
        # top from the whole glyph: in Å the ring is merged with the apex and only its
        # counter is a contour of its own
        out[name] = ((x0 + x1) / 2, (y0 + y1) / 2, _bounds(gs, name)[3])    # centre, and top
    return out


def _anchor(x, y):
    a = ot.Anchor()
    a.Format = 1
    a.XCoordinate, a.YCoordinate = round(x), round(y)
    return a


def _lookup(lookup_type, subtable):
    lk = ot.Lookup()
    lk.LookupType = lookup_type
    lk.LookupFlag = 0
    lk.SubTable = [subtable]
    lk.SubTableCount = 1
    return lk


def draft_stacks(style, variant, out_path=None):
    """Patched font of `style` with the stacking lookups of `variant`; returns (font, info)."""
    key = style + "_patch"
    tt = TTFont(str(FONTS[key]["path"]))
    gs, t = tt.getGlyphSet(), SLANT[style]
    main = _main_lookup(tt, key)
    glyph_map = tt.getReverseGlyphMap()
    target = targets(tt, key, variant)

    # second marks: anchor at (axis X at that height, ink bottom - gap)
    attach = {}
    for _, g, _ in mark_glyphs(tt):
        _, mx, my = _mark_anchor(main, g)
        y = _bounds(gs, g)[1] - target[g]
        attach[g] = (0, _anchor(mx + (y - my) * t, y))
    # first marks: stack anchor at the ink top, on the mark's axis
    stack_marks = {}
    for _, g, _ in mark_glyphs(tt):
        _, mx, my = _mark_anchor(main, g)
        y = _bounds(gs, g)[3]
        stack_marks[g] = {0: _anchor(mx + (y - my) * t, y)}
    # precomposed letters: stack anchor at the top of the mark ink, on its centre
    bases = {}
    for name, (cx, cy, top) in stack_bases(tt).items():
        bases[name] = {0: _anchor(cx + (top - cy) * t, top)}

    # mark-to-mark: MarkMarkPos has the MarkBasePos layout with Mark1/Mark2 names
    mb = buildMarkBasePosSubtable(attach, stack_marks, glyph_map)
    mm = ot.MarkMarkPos()
    mm.Format = 1
    mm.Mark1Coverage, mm.Mark2Coverage = mb.MarkCoverage, mb.BaseCoverage
    mm.ClassCount, mm.Mark1Array = mb.ClassCount, mb.MarkArray
    m2 = ot.Mark2Array()
    m2.Mark2Record = []
    for rec in mb.BaseArray.BaseRecord:
        r = ot.Mark2Record()
        r.Mark2Anchor = rec.BaseAnchor
        m2.Mark2Record.append(r)
    m2.Mark2Count = len(m2.Mark2Record)
    mm.Mark2Array = m2
    stack_base = buildMarkBasePosSubtable(attach, bases, glyph_map)

    gpos = tt["GPOS"].table
    lookups = gpos.LookupList.Lookup
    lookups += [_lookup(6, mm), _lookup(4, stack_base)]
    gpos.LookupList.LookupCount = len(lookups)
    i_mkmk, i_base = len(lookups) - 2, len(lookups) - 1
    tags = {fr.FeatureTag for fr in gpos.FeatureList.FeatureRecord}
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag == "mkmk":
            fr.Feature.LookupListIndex = [i_mkmk]
        elif fr.FeatureTag == "mark":
            fr.Feature.LookupListIndex = fr.Feature.LookupListIndex + [i_base]
        fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
    if "mkmk" not in tags:   # semibold italic: add the feature to every language system
        f = ot.Feature()
        f.FeatureParams = None
        f.LookupListIndex = [i_mkmk]
        f.LookupCount = 1
        fr = ot.FeatureRecord()
        fr.FeatureTag, fr.Feature = "mkmk", f
        gpos.FeatureList.FeatureRecord.append(fr)
        gpos.FeatureList.FeatureCount = len(gpos.FeatureList.FeatureRecord)
        idx = len(gpos.FeatureList.FeatureRecord) - 1
        for sr in gpos.ScriptList.ScriptRecord:
            for ls in [sr.Script.DefaultLangSys] + [l.LangSys for l in sr.Script.LangSysRecord]:
                if ls is not None:
                    ls.FeatureIndex.append(idx)
                    ls.FeatureCount = len(ls.FeatureIndex)
        # feature records must stay sorted by tag
        order = sorted(range(len(gpos.FeatureList.FeatureRecord)),
                       key=lambda k: gpos.FeatureList.FeatureRecord[k].FeatureTag)
        remap = {old: new for new, old in enumerate(order)}
        gpos.FeatureList.FeatureRecord = [gpos.FeatureList.FeatureRecord[k] for k in order]
        for sr in gpos.ScriptList.ScriptRecord:
            for ls in [sr.Script.DefaultLangSys] + [l.LangSys for l in sr.Script.LangSysRecord]:
                if ls is not None:
                    ls.FeatureIndex = sorted(remap[k] for k in ls.FeatureIndex)
    if out_path:
        save_renamed(tt, out_path)
    return tt, {"targets": target, "bases": sorted(bases), "gaps": gaps(tt, key)}
