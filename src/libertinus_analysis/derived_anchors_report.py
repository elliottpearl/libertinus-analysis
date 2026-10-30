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
the base letter in the patched font, and the outline shift and match.
"""

from fontTools.ttLib import TTFont

from .font_context import FONTS
from .font_patching_anchors import load_human_anchors
from .font_patching_derivedanchors import (
    MIN_MATCH,
    load_derived_letters,
    inherited_anchor,
    outline_shift,
    style_classes,
)
from .fontmetrics_helpers import get_anchor_candidate
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
    (a tuple, or a per-style dict); and derived_by_name for the dotless forms.
    """
    derived, derived_by_name = load_derived_letters()
    cols = [(cp, base_cp, classes) for cp, (base_cp, classes) in derived.items()]
    return cols, derived_by_name

def _style_block(style_key, cols, derived_by_name):
    meta = FONTS[style_key]
    li = meta["lookup_index"]
    orig = TTFont(meta["path"])
    patched_path = meta["path"].with_name(f"{meta['path'].stem}-patch{meta['path'].suffix}")
    patched = TTFont(patched_path)
    cmap = orig.getBestCmap()
    orig_anchors = _anchors(orig, li)
    patch_anchors = _anchors(patched, li)
    metrics = load_fontmetrics(style_key)
    human = load_human_anchors(style_key)

    rows = {k: [] for k in ("orig", "patch", "base", "shift",
                            "a", "a?", "a<", "a!", "b", "b?", "b<", "b!")}
    for cp, base_cp, classes in cols:
        rows["orig"].append(_sample(cp, style_key))
        rows["patch"].append(_sample(cp, f"{style_key}_patch"))
        rows["base"].append(_sample(base_cp, f"{style_key}_patch"))
        if cp not in cmap or base_cp not in cmap:
            for k in rows:
                if k not in ("orig", "patch", "base"):
                    rows[k].append("")
            continue

        dg, bg = cmap[cp], cmap[base_cp]
        dx, match = outline_shift(orig, dg, bg)
        shift_cell = f"{dx:+d}, {match:.0%}".replace("%", "\\%")
        if match < MIN_MATCH:
            shift_cell = f"\\textit{{{shift_cell}}}"
        rows["shift"].append(shift_cell)

        for cls, prefix in ((0, "a"), (2, "b")):
            # an above mark attaches to the dotless form, if one is listed
            g, b, m, s = dg, bg, match, dx
            dotless = f"{dg}.dotless"
            if cls == 0 and dotless in derived_by_name and cls in style_classes(derived_by_name[dotless][1], style_key):
                g, b = dotless, derived_by_name[dotless][0]
                s, m = outline_shift(orig, g, b)
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
                rows[f"{prefix}<"].append("")
                continue
            ix, iy, _ = inherited_anchor(orig, style_key, g, b, base_xy, cls, s)
            inh = (ix, iy)
            applied = (m >= MIN_MATCH and not curated
                       and patch_anchors.get(g, {}).get(cls) == inh)
            rows[f"{prefix}<"].append(_xy(inh, bold=applied))

    label = STYLE_LABELS[style_key]
    out = [["\\hline " + label] + rows["orig"]]
    for k in ("patch", "base", "shift", "a", "a?", "a<", "a!", "b", "b?", "b<", "b!"):
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
