# fontmetrics_report.py
from __future__ import annotations

from .fontmetrics_loader import (
    load_all_fontmetrics,
    load_fontmetrics,
    get_anchor,
    get_bbox,
)
from .fontmetrics_helpers import (
    get_anchor_candidate,
    get_unicode_category,
)
from .tex_helpers import (
    latex_font_style,
)

# ----------------------------------------------------------------------
# Shared helpers (lightweight, no classes)
# ----------------------------------------------------------------------

STYLE_KEYS = ["regular", "italic", "semibold", "semibold_italic"]

STYLE_LABELS = {
    "regular": "reg",
    "italic": "it",
    "semibold": "sb",
    "semibold_italic": "si",
}

# Invisible strut for the glyph-sample rows: an ordinary row is too short for
# a capital with an above mark or a descender with a below mark.
SAMPLE_STRUT = "\\rule[-0.5em]{0pt}{1.9em}"


def texify(rows):
    """Convert list-of-list rows into TeX table body."""
    return " \\\\\n".join(" & ".join(c) for c in rows) + " \\\\\n"


def build_header_rows(cps):
    """hex + category rows (shared by letters and marks)."""
    return [
        ["hex"] + [f"{cp:04X}" for cp in cps],
        ["cat"] + [get_unicode_category(cp) for cp in cps],
    ]


def extract_anchor_xy(style_metrics, cps, anchor_id):
    """Shared anchor extraction logic."""
    xs, ys = [], []
    for cp in cps:
        anchor = get_anchor(style_metrics, cp, anchor_id)
        if anchor:
            xs.append(str(int(anchor[0])))
            ys.append(str(int(anchor[1])))
        else:
            xs.append("")
            ys.append("")
    return xs, ys


def apply_style(style_key, raw):
    """Shared style wrapper (regular vs styled, original vs patched)."""
    if style_key == "regular":
        return raw
    return latex_font_style(style_key, raw)


def xy_cell(x, y):
    """One cell holding an X, Y pair."""
    return f"{round(x)}, {round(y)}"


# ----------------------------------------------------------------------
# Glyph sample for letters (CGJ version)
# ----------------------------------------------------------------------

def sample_letter_glyph(cp: int, style_key: str) -> str:
    raw = (
        f'\\char"{cp:04X} '
        f'\\char"{cp:04X}\\cgj\\char"0307 '
        f'\\char"{cp:04X}\\cgj\\char"0331'
    )
    return apply_style(style_key, raw)


# ----------------------------------------------------------------------
# Main table for letters
# ----------------------------------------------------------------------

def make_fontmetrics_table(bases: list[str]) -> str:
    """
    One column per base; per style a block of rows: glyph samples in the
    original and patched fonts, the ideal bounding box, then for the above (a)
    and below (b) anchor the font's anchor, the candidate (?) and anchor minus
    candidate (delta). Anchor and candidate cells hold "X, Y".
    """
    cps = [ord(cp) for cp in bases]
    all_metrics = load_all_fontmetrics()

    rows = []

    # Header rows
    rows.extend(build_header_rows(cps))

    # Style blocks
    for style_key in STYLE_KEYS:
        style_label = STYLE_LABELS[style_key]
        style_metrics = all_metrics[style_key]

        rows.append(["\\hline " + style_label + SAMPLE_STRUT] + [sample_letter_glyph(cp, style_key) for cp in cps])
        rows.append(["patch" + SAMPLE_STRUT] + [sample_letter_glyph(cp, f"{style_key}_patch") for cp in cps])

        anchor_rows = {}
        ideals = {}
        for anchor_id, prefix in [("0", "a"), ("2", "b")]:
            have, want, delta, ideal = [], [], [], []
            for cp in cps:
                anchor = get_anchor(style_metrics, cp, anchor_id)
                cand = get_anchor_candidate(style_key, style_metrics, cp, anchor_id)
                have.append(xy_cell(*anchor) if anchor else "")
                want.append(xy_cell(cand[0], cand[1]) if cand else "")
                ideal.append(cand[2] if cand else "")
                if anchor and cand:
                    delta.append(xy_cell(anchor[0] - cand[0], anchor[1] - cand[1]))
                else:
                    delta.append("")
            anchor_rows[prefix] = (have, want, delta)
            ideals[prefix] = ideal

        ideal = [f"{t}, {b}" if t and b else "" for t, b in zip(ideals["a"], ideals["b"])]
        rows.append(["ideal"] + ideal)

        for prefix in ("a", "b"):
            have, want, delta = anchor_rows[prefix]
            rows.append([prefix] + have)
            rows.append([f"{prefix}?"] + want)
            rows.append([f"{prefix}$\\delta$"] + delta)

    return texify(rows)


# ----------------------------------------------------------------------
# Marks table
# ----------------------------------------------------------------------

# Anchor class to read for each kind of mark table. Semibold puts the dot,
# diaeresis, ring, hook and comma above in a second above class, "1".
MARK_CLASSES = {"0": ["0", "1"], "2": ["2"]}

# Stage 1 of the patch merges semibold's class 1 (top_punkt) into class 0,
# raising its mark anchors by the difference between the two classes' base anchors.
TOP_PUNKT_RAISE = 96


def sample_mark_glyph(cp: int, style_key: str) -> str:
    """The mark on an x-height base and on a capital (CGJ blocks composition)."""
    raw = f'n\\cgj\\char"{cp:04X} H\\cgj\\char"{cp:04X}'
    return apply_style(style_key, raw)


def make_fontmetrics_table_for_marks(marks: list[str], anchor_id: str) -> str:
    """
    One column per mark; per style a block of rows: the mark on n and H in the
    original and patched fonts, then the mark's anchor in the original font (m)
    and in the patched font (mp), and patched minus original (m delta), as
    "X, Y". An original anchor in a class other than anchor_id is marked with
    its class in parentheses; for semibold's class 1, merged into class 0 with
    its anchor raised by 96, the delta is taken from the raised anchor, so it
    shows how far the mark moves.
    """
    cps = [ord(cp) for cp in marks]
    all_metrics = load_all_fontmetrics()

    rows = build_header_rows(cps)

    for style_key in STYLE_KEYS:
        style_label = STYLE_LABELS[style_key]
        style_metrics = all_metrics[style_key]
        patch_metrics = load_fontmetrics(f"{style_key}_patch")

        rows.append(["\\hline " + style_label + SAMPLE_STRUT] + [sample_mark_glyph(cp, style_key) for cp in cps])
        rows.append(["patch" + SAMPLE_STRUT] + [sample_mark_glyph(cp, f"{style_key}_patch") for cp in cps])

        have, patched, delta = [], [], []
        for cp in cps:
            anchor, cls = None, anchor_id
            for c in MARK_CLASSES[anchor_id]:
                anchor = get_anchor(style_metrics, cp, c)
                if anchor:
                    cls = c
                    break
            new = get_anchor(patch_metrics, cp, anchor_id)
            note = f" ({cls})" if cls != anchor_id else ""
            have.append(xy_cell(*anchor) + note if anchor else "")
            patched.append(xy_cell(*new) if new else "")
            if anchor and new:
                raise_y = TOP_PUNKT_RAISE if cls == "1" else 0
                dx, dy = new[0] - anchor[0], new[1] - anchor[1] - raise_y
                delta.append(xy_cell(dx, dy) if (round(dx), round(dy)) != (0, 0) else "")
            elif new:
                delta.append("new")
            else:
                delta.append("")

        rows.append(["m"] + have)
        rows.append(["mp"] + patched)
        rows.append(["m$\\delta$"] + delta)

    return texify(rows)


# ----------------------------------------------------------------------
# Letters whose anchors are all inherited (stages 8 and 9)
# ----------------------------------------------------------------------

def inherited_only(cps: list[int]) -> set[int]:
    """
    The codepoints whose above and below anchors in the patched fonts were all
    set by stage 8 (derived letters) or stage 9 (precomposed letters), in every
    style, as recorded by the patch in data/anchor_provenance/{style}.json.
    A letter that keeps a designer, curated or heuristic anchor in any style,
    or has no anchor at all, is not among them.
    """
    import json
    from fontTools.ttLib import TTFont
    from .font_context import FONTS
    from .font_patching import INHERITED_DIR, _base_anchors

    status = {cp: {"inherited": False, "other": False} for cp in cps}
    for style_key in STYLE_KEYS:
        record = json.loads((INHERITED_DIR / f"{style_key}.json").read_text(encoding="utf-8"))
        inherited = {(g, c) for g, c in record["derived"] + record["precomposed"]}
        meta = FONTS[f"{style_key}_patch"]
        ttfont = TTFont(meta["path"])
        cmap = ttfont.getBestCmap()
        anchors = _base_anchors(ttfont, meta["lookup_index"])
        for cp in cps:
            glyph = cmap.get(cp)
            for cls in (0, 2):
                if glyph and (glyph, cls) in anchors:
                    status[cp]["inherited" if (glyph, cls) in inherited else "other"] = True
    return {cp for cp, st in status.items() if st["inherited"] and not st["other"]}


# ----------------------------------------------------------------------
# LaTeX wrapper (unchanged)
# ----------------------------------------------------------------------

from string import Template

def wrap_in_table_environment(table_body: str, caption: str, label: str,
                              size: str = "footnotesize", colsep: str = "3.5pt") -> str:
    try:
        first_row = table_body.strip().split("\\\\")[0]
        cols = first_row.count("&") + 1
    except Exception:
        cols = 1

    colspec = "l" + ("r" * (cols - 1))

    template = Template(
        r"""
\begin{table}[p]
\captionsetup{justification=raggedright, singlelinecheck=false}
\caption{$caption}
\label{$label}
\setlength{\tabcolsep}{$colsep}

{\$size
\begin{tabular}{$colspec}
$table_body
\end{tabular}
}
\end{table}
\clearpage
"""
    )

    return template.substitute(
        caption=caption,
        label=label,
        colspec=colspec,
        table_body=table_body,
        size=size,
        colsep=colsep,
    )
