# fontmetrics_report.py
from __future__ import annotations

from .fontmetrics_loader import (
    load_all_fontmetrics,
    get_anchor,
    get_bbox,
)
from .fontmetrics_helpers import (
    get_anchor_candidate,
    get_mark_anchor_candidate,
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


def sample_mark_glyph(cp: int, style_key: str) -> str:
    """The mark on an x-height base and on a capital (CGJ blocks composition)."""
    raw = f'n\\cgj\\char"{cp:04X} H\\cgj\\char"{cp:04X}'
    return apply_style(style_key, raw)


def make_fontmetrics_table_for_marks(marks: list[str], anchor_id: str) -> str:
    """
    One column per mark; per style a block of rows: the mark on n and H in the
    original and patched fonts, then the mark's anchor (m), its candidate (m?)
    and anchor minus candidate (m delta), as "X, Y". An anchor in a class
    other than anchor_id is marked with its class in parentheses.
    """
    cps = [ord(cp) for cp in marks]
    all_metrics = load_all_fontmetrics()

    rows = build_header_rows(cps)

    for style_key in STYLE_KEYS:
        style_label = STYLE_LABELS[style_key]
        style_metrics = all_metrics[style_key]

        rows.append(["\\hline " + style_label + SAMPLE_STRUT] + [sample_mark_glyph(cp, style_key) for cp in cps])
        rows.append(["patch" + SAMPLE_STRUT] + [sample_mark_glyph(cp, f"{style_key}_patch") for cp in cps])

        have, want, delta = [], [], []
        for cp in cps:
            anchor, cls = None, anchor_id
            for c in MARK_CLASSES[anchor_id]:
                anchor = get_anchor(style_metrics, cp, c)
                if anchor:
                    cls = c
                    break
            cand = get_mark_anchor_candidate(style_key, style_metrics, cp, cls)
            note = f" ({cls})" if cls != anchor_id else ""
            have.append(xy_cell(*anchor) + note if anchor else "")
            want.append(xy_cell(*cand) if cand else "")
            if anchor and cand:
                delta.append(xy_cell(anchor[0] - cand[0], anchor[1] - cand[1]))
            else:
                delta.append("")

        rows.append(["m"] + have)
        rows.append(["m?"] + want)
        rows.append(["m$\\delta$"] + delta)

    return texify(rows)


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
