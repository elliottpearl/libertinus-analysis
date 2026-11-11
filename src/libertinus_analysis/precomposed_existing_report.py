"""
precomposed_existing_report.py

Every precomposed letter in stage 9's lists (data/precomposed_letters.py) that
has an anchor stage 9 does not set: a designer anchor (from the original font)
or a curated one (data/fontanchors_human/{style}.py). For each, the anchor
stage 9 would inherit instead (the base letter's final anchor in the patched
font, moved by fit_base), and the difference. Designer anchors deleted by a
"delete" override (data/fontanchors_audit/overrides.py) are listed with their
original value; stage 9 has inherited them since.

Written to tex/input/precomposed_existing.tex, a check for anchors to delete;
the report's "Precomposed characters" section \\input it until 2026-11-10.
"""

from fontTools.ttLib import TTFont

from .config import TEX_INPUT_DIR
from .font_context import FONTS
from .font_patching_anchors import load_human_anchors
from .font_patching_deleteanchors import load_audit_overrides
from . import font_patching_precomposed_anchors as stage9
from .font_patching_inherit import fit_base

STYLES = ("regular", "italic", "semibold", "semibold_italic")
STYLE_LABEL = {
    "regular": "Regular", "italic": "Italic",
    "semibold": "Semibold", "semibold_italic": "Semibold italic",
}
STYLE_FONT = {
    "regular": r"\LibertinusSerifPatch",
    "italic": r"\LibertinusSerifPatch\itshape",
    "semibold": r"\LibertinusSerifPatch\bfseries",
    "semibold_italic": r"\LibertinusSerifPatch\bfseries\itshape",
}
ROWS_PER_COLUMN = 40
COLUMNS_PER_TABLE = 4


def _anchors(ttfont, lookup_index):
    sub = ttfont["GPOS"].table.LookupList.Lookup[lookup_index].SubTable[0]
    return {
        g: {i: (a.XCoordinate, a.YCoordinate) for i, a in enumerate(rec.BaseAnchor) if a}
        for g, rec in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord)
    }


def collect_rows(style):
    """Rows (letter cp, class, base cp, source, anchor, stage-9 anchor, fit, deleted)."""
    fk = f"{style}_patch"
    font = TTFont(FONTS[fk]["path"])
    cmap = font.getBestCmap()
    final = _anchors(font, FONTS[fk]["lookup_index"])
    orig_font = TTFont(FONTS[style]["path"])
    orig_cmap = orig_font.getBestCmap()
    orig = _anchors(orig_font, FONTS[style]["lookup_index"])
    human = load_human_anchors(style)
    cur_cp, cur_name = human.get("bases", {}), human.get("bases_by_name", {})
    overrides = load_audit_overrides(style)

    rows = []
    for cls, (cps, _excluded) in stage9.load_precomposed_letters().items():
        for cp in cps:
            g = cmap.get(cp)
            if g is None:
                continue
            o = orig.get(orig_cmap.get(cp), {}).get(cls)
            curated = cls in cur_cp.get(cp, {}) or cls in cur_name.get(g, {})
            deleted = overrides.get(g, {}).get(cls) == "delete"
            if o is None and not curated:
                continue
            if curated:
                source, anchor = "curated", final[g][cls]
            elif deleted:
                source, anchor = "designer", o
            else:
                source, anchor = "designer", final.get(g, {}).get(cls, o)
            base_cp = stage9.get_base_cp_from_unicode(cp)
            if cls == 2 and base_cp in stage9.DOTLESS_SOURCE:
                base_cp = stage9.DOTLESS_SOURCE[base_cp]
            base_g = cmap.get(base_cp)
            base_xy = final.get(base_g, {}).get(cls)
            if base_xy is None:
                rows.append((cp, cls, base_cp, source, anchor, None, None, deleted))
                continue
            dx, match, _scale = fit_base(font, style, g, base_g, cls, base_xy)
            rows.append((cp, cls, base_cp, source, anchor,
                         (base_xy[0] + dx, base_xy[1]), match, deleted))
    return rows


def _key(row):
    _cp, _cls, _b, _s, a, p, _m, _d = row
    if p is None:
        return (1, 0)
    return (0, -max(abs(a[0] - p[0]), abs(a[1] - p[1])), row[0])


def _cell(style, row):
    cp, cls, base_cp, source, a, p, match, deleted = row
    font = STYLE_FONT[style]
    side = "a" if cls == 0 else "b"
    letter = f"{{{font} \\char\"{cp:04X}}}"
    base = f"{{{font} \\char\"{base_cp:04X}}}"
    src = ("c" if source == "curated" else "d") + ("$\\to$9" if deleted else "")
    have = f"{a[0]}, {a[1]}"
    if p is None:
        return f"{letter} & {side} & {base} & {src} & {have} & & & & "
    dx, dy = a[0] - p[0], a[1] - p[1]
    big = max(abs(dx), abs(dy)) > 10
    fmt = (lambda v: f"\\textbf{{{v:+d}}}") if big else (lambda v: f"{v:+d}")
    return (f"{letter} & {side} & {base} & {src} & {have} & {p[0]}, {p[1]} & "
            f"{fmt(dx) if dx else '0'} & {fmt(dy) if dy else '0'} & {round(match * 100)}")


def latex_for_style(style, rows):
    rows = sorted(rows, key=_key)
    cols = [rows[i:i + ROWS_PER_COLUMN] for i in range(0, len(rows), ROWS_PER_COLUMN)]
    heading = f"\\textbf{{{STYLE_LABEL[style]}: {len(rows)} letters}}\\par\\smallskip"
    head = (r"\begin{tabular}[t]{@{}c@{\,}c@{\,}c@{\;}l@{\;}r@{\;}r@{\;}r@{\,}r@{\;}r@{}}" "\n"
            r"& & base & & anchor & stage 9 & $\Delta x$ & $\Delta y$ & fit\\ \hline")
    out = []
    for t in range(0, len(cols), COLUMNS_PER_TABLE):
        # one box per block of columns, the style's heading in the first, so that
        # a heading never ends a page without its table
        out.append("\\par\\medskip\\noindent\\begin{minipage}[t]{\\textwidth}")
        if t == 0:
            out.append(heading)
        out.append("{\\footnotesize")
        parts = []
        for col in cols[t:t + COLUMNS_PER_TABLE]:
            body = " \\\\\n".join(_cell(style, r) for r in col)
            parts.append(f"{head}\n{body}\n\\end{{tabular}}")
        out.append("\\hspace{3em}\n".join(parts))
        out.append("}\n\\end{minipage}\n")
    return "\n".join(out)


def write_report(outfile="precomposed_existing.tex"):
    chunks = [
        "% Generated by run_precomposed_existing_report.py; do not edit.",
    ]
    total = 0
    for style in STYLES:
        rows = collect_rows(style)
        total += len(rows)
        chunks.append(latex_for_style(style, rows))
    chunks.append("\\par\\medskip")
    path = TEX_INPUT_DIR / outfile
    path.write_text("\n".join(chunks) + "\n")
    return path, total
