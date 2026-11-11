# derived_anchors_report.py
"""
Test sheet for the derived-letter stage (font_patching_derivedanchors.py).

One column per derived letter of data/derived_letters.py; per style a block
of rows comparing, for the above (a) and below (b) anchor, the methods that
could set it:

    a      the designer's anchor (original font)
    a?     the heuristic candidate (get_anchor_candidate)
    a<     the base letter's final anchor (patched font) plus the outline
           shift, with y moved where the derived letter reaches further into
           the mark's zone: what stage 8 inherits; bold where the patched
           font has it
    a!     a curated anchor, which stage 8 never overwrites

plus samples of the derived letter in the original and patched fonts and of
the base letter in the patched font, and per class (a~, b~) the shift and fit
that stage 8 uses: fit_base's shift and fit; "s" for the stem match of the
bottom-tail letters; "|" for the stem-midline shift of stem_axis letters.

make_stem_check_table() is the stem-midline check of the l-like and i-like
letters: how far each above and below anchor's mark axis lies from the
letter's own stem midline.
"""

from fontTools.ttLib import TTFont

from .font_context import FONTS
from .font_patching_anchors import load_human_anchors
from .font_patching_derivedanchors import (
    WIDE_SCALE_DEV,
    MIN_MATCH,
    load_derived_letters,
    inherited_anchor,
    load_stem_axis,
    load_stem_match,
    stem_axis_shift,
    stem_midline,
    stem_shift,
    tail_anchor,
    style_classes,
)
from .font_patching_inherit import MIN_FIT, fit_base
from .fontmetrics_helpers import SLOPE, get_anchor_candidate
from .fontmetrics_loader import load_fontmetrics
from .fontmetrics_report import STYLE_KEYS, STYLE_LABELS, apply_style, texify

ABOVE_MARK, BELOW_MARK = 0x0302, 0x0331  # circumflex, macron below

def _anchors(ttfont, lookup_index):
    """{glyph name: {class: (x, y)}} of the mark-to-base lookup."""
    sub = ttfont["GPOS"].table.LookupList.Lookup[lookup_index].SubTable[0]
    out = {}
    for g, rec in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
        out[g] = {
            i: (a.XCoordinate, a.YCoordinate)
            for i, a in enumerate(rec.BaseAnchor) if a is not None
        }
    return out

def _sample(cp, style_key):
    raw = (
        f'\\char"{cp:04X}\\cgj\\char"{ABOVE_MARK:04X} '
        f'\\char"{cp:04X}\\cgj\\char"{BELOW_MARK:04X}'
    )
    return apply_style(style_key, raw)

def _xy(xy, bold=False):
    if xy is None:
        return ""
    cell = f"{round(xy[0])}, {round(xy[1])}"
    return f"\\textbf{{{cell}}}" if bold else cell

def _columns():
    """
    [(derived cp, base cp, classes)], classes as in data/derived_letters.py
    (a tuple, or a per-style dict), ordered by base letter, then by codepoint,
    as the grids; and derived_by_name for the dotless forms.
    """
    derived, derived_by_name = load_derived_letters()
    cols = sorted(((cp, base_cp, classes) for cp, (base_cp, classes) in derived.items()),
                  key=lambda c: (c[1], c[0]))
    return cols, derived_by_name

def _fit_cell(dx, match, threshold, marker=""):
    if match is None:
        cell = f"{dx:+d}{marker}"
    else:
        cell = f"{dx:+d}, {match:.0%}{marker}".replace("%", "\\%")
    if match is not None and match < threshold:
        cell = f"\\textit{{{cell}}}"
    return cell

def _style_block(style_key, cols, derived_by_name):
    meta = FONTS[style_key]
    li = meta["lookup_index"]
    orig = TTFont(meta["path"])
    patched_path = meta["path"].with_name(f"{meta['path'].stem}-patch{meta['path'].suffix}")
    patched = TTFont(patched_path)  # outlines as stage 8 sees them (stage 2 redraws some)
    cmap = patched.getBestCmap()
    orig_cmap = orig.getBestCmap()
    orig_anchors = _anchors(orig, li)
    patch_anchors = _anchors(patched, li)
    metrics = load_fontmetrics(style_key)
    human = load_human_anchors(style_key)
    stem_match, stem_axis = load_stem_match(), load_stem_axis()

    rows = {k: [] for k in ("orig", "patch", "base",
                            "a~", "a", "a?", "a<", "a!", "b~", "b", "b?", "b<", "b!")}
    for cp, base_cp, classes in cols:
        rows["orig"].append(_sample(cp, style_key) if cp in orig_cmap else "")
        rows["patch"].append(_sample(cp, f"{style_key}_patch"))
        rows["base"].append(_sample(base_cp, f"{style_key}_patch"))
        if cp not in cmap or base_cp not in cmap:
            for k in rows:
                if k not in ("orig", "patch", "base"):
                    rows[k].append("")
            continue

        dg, bg = cmap[cp], cmap[base_cp]
        tail = cp in stem_match
        if tail:
            # stems above the tail, at the base letter's above (else below) axis
            axis_xy = patch_anchors.get(bg, {}).get(0) or patch_anchors.get(bg, {}).get(2) or (0, 0)
            axis = axis_xy[0] - axis_xy[1] * SLOPE[style_key]
            tail_dx, tail_m = stem_shift(patched, style_key, dg, bg, axis)
            if tail_m < MIN_MATCH:  # the patch's second try, a wider scale
                wide = stem_shift(patched, style_key, dg, bg, axis, WIDE_SCALE_DEV)
                if wide[1] >= MIN_MATCH:
                    tail_dx, tail_m = wide

        for cls, prefix in ((0, "a"), (2, "b")):
            # an above mark attaches to the dotless form, if one is listed
            g, b = dg, bg
            dotless = f"{dg}.dotless"
            if cls == 0 and dotless in derived_by_name and cls in style_classes(derived_by_name[dotless][1], style_key):
                g, b = dotless, derived_by_name[dotless][0]
                listed = True
            else:
                listed = cls in style_classes(classes, style_key)

            rows[prefix].append(_xy(orig_anchors.get(g, {}).get(cls)))
            cand = get_anchor_candidate(style_key, metrics, cp, str(cls))
            rows[f"{prefix}?"].append(_xy(cand[:2] if cand else None))

            curated = (human.get("bases", {}).get(cp, {}).get(cls)
                       or human.get("bases_by_name", {}).get(g, {}).get(cls))
            rows[f"{prefix}!"].append(_xy(curated))

            base_xy = patch_anchors.get(b, {}).get(cls)
            if not listed or base_xy is None:
                rows[f"{prefix}~"].append("")
                rows[f"{prefix}<"].append("")
                continue
            if tail and g == dg:
                rows[f"{prefix}~"].append(_fit_cell(tail_dx, tail_m, MIN_MATCH, " s"))
                inh, _ = tail_anchor(patched, style_key, cp, g, b, base_xy, cls)
                if inh is None:
                    rows[f"{prefix}<"].append("")
                    continue
                applied = not curated and patch_anchors.get(g, {}).get(cls) == tuple(inh)
            else:
                if cp in stem_axis and g == dg:
                    dx, ok = stem_axis_shift(patched, style_key, g, b), True
                    rows[f"{prefix}~"].append("" if dx is None else _fit_cell(dx, None, 0, " |"))
                    ok = dx is not None
                else:
                    dx, m, _ = fit_base(patched, style_key, g, b, cls, base_xy)
                    rows[f"{prefix}~"].append(_fit_cell(dx, m, MIN_FIT))
                    ok = m >= MIN_FIT
                if dx is None:
                    rows[f"{prefix}<"].append("")
                    continue
                ix, iy, _ = inherited_anchor(patched, style_key, g, b, base_xy, cls, dx)
                inh = (ix, iy)
                applied = ok and not curated and patch_anchors.get(g, {}).get(cls) == inh
            rows[f"{prefix}<"].append(_xy(inh, bold=applied))

    label = STYLE_LABELS[style_key]
    out = [["\\hline " + label] + rows["orig"]]
    for k in ("patch", "base", "a~", "a", "a?", "a<", "a!", "b~", "b", "b?", "b<", "b!"):
        out.append([k] + rows[k])
    return out

def make_derived_anchors_tables(max_cols=16):
    """Return LaTeX for all tables (tabular bodies wrapped in table floats)."""
    from .fontmetrics_report import wrap_in_table_environment

    cols, derived_by_name = _columns()
    n = len(cols)
    parts = -(-n // max_cols)
    size = -(-n // parts)
    chunks = [cols[i:i + size] for i in range(0, n, size)]

    tables = []
    for idx, chunk in enumerate(chunks, start=1):
        rows = [
            ["hex"] + [f"{cp:04X}" for cp, _, _ in chunk],
            ["base"] + [f"{b:04X}" for _, b, _ in chunk],
        ]
        for style_key in STYLE_KEYS:
            rows.extend(_style_block(style_key, chunk, derived_by_name))
        tables.append(wrap_in_table_environment(
            texify(rows),
            caption=f"Derived letters and inherited anchors {idx}/{len(chunks)}",
            label=f"table:derived_anchors_{idx}",
            size="scriptsize",
            colsep="2.5pt",
        ))
    return "\n".join(tables)

# l-like and i-like letters for the stem-midline check, by glyph name where unencoded
STEM_CHECK = [0x006C, 0x013A, 0x013C, 0x013E, 0x0140, 0x0142, 0x019A, 0x026B, 0x026C, 0x026D,
              0x026E, 0x2C61, 0x0069, 0x0131, 0x0268, "uni0268.dotless", 0x0269]
STEM_TOL_CHECK = 5  # an offset beyond this is printed in bold

def make_stem_check_table():
    """
    LaTeX table: per style, the offset of each above (a) and below (b)
    anchor's mark axis (sheared, with K) from the letter's own stem midline
    (stem_midline in font_patching_derivedanchors.py), in the patched fonts.
    Offsets beyond STEM_TOL_CHECK are bold.
    """
    from .fontmetrics_helpers import SHIFT_K
    from .fontmetrics_report import wrap_in_table_environment

    def label(item):
        return f'\\char"{item:04X}' if isinstance(item, int) else "ɨ.dl"

    rows = [["", *(label(i) for i in STEM_CHECK)],
            ["hex", *(f"{i:04X}" if isinstance(i, int) else "dotless" for i in STEM_CHECK)]]
    for style_key in STYLE_KEYS:
        meta = FONTS[f"{style_key}_patch"]
        font = TTFont(meta["path"])
        cmap = font.getBestCmap()
        anchors = _anchors(font, meta["lookup_index"])
        slope = SLOPE[style_key]
        cells = {0: [], 2: []}
        for item in STEM_CHECK:
            g = cmap.get(item) if isinstance(item, int) else item
            mid = stem_midline(font, style_key, g) if g else None
            for cls in (0, 2):
                xy = anchors.get(g, {}).get(cls) if g else None
                if xy is None or mid is None:
                    cells[cls].append("")
                    continue
                k = SHIFT_K.get(style_key, {}).get(str(cls), 0)
                off = round(xy[0] - xy[1] * slope + k - mid)
                cell = f"{off:+d}"
                cells[cls].append(f"\\textbf{{{cell}}}" if abs(off) > STEM_TOL_CHECK else cell)
        rows.append([f"\\hline {STYLE_LABELS[style_key]} a", *cells[0]])
        rows.append(["b", *cells[2]])
    return wrap_in_table_environment(
        texify(rows),
        caption="Stem-midline check: offset of the mark axis from the stem midline, patched fonts",
        label="table:stem_check",
        size="scriptsize",
        colsep="2.5pt",
    )
