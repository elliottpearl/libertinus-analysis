# fontmetrics_report.py
from __future__ import annotations

from .fontmetrics_loader import (
    load_all_fontmetrics,
    get_anchor,
    get_bbox,
)
from .fontmetrics_helpers import (
    get_mid_x_for_style,
    compute_dx,
    get_upright_mid_x,
    get_unicode_category,
    get_ideal_above_aspect,
    get_ideal_below_aspect,
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
    """Shared style wrapper (regular vs styled)."""
    if style_key == "regular":
        return raw
    return latex_font_style(style_key, raw)


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
    cps = [ord(cp) for cp in bases]
    all_metrics = load_all_fontmetrics()

    rows = []

    # Header rows
    rows.extend(build_header_rows(cps))

    # Style blocks
    for style_key in STYLE_KEYS:
        style_label = STYLE_LABELS[style_key]
        style_metrics = all_metrics[style_key]

        # Glyph row
        glyphs = [sample_letter_glyph(cp, style_key) for cp in cps]
        rows.append([style_label] + glyphs)

        # Ideal aspect rows
        aa = []
        ba = []
        for cp in cps:
            bbox = get_bbox(style_metrics, cp)
            if bbox:
                ymin, ymax = bbox[1], bbox[3]
                aa.append(get_ideal_above_aspect(style_key, ymax, cp))
                ba.append(get_ideal_below_aspect(style_key, ymin))
            else:
                aa.append("")
                ba.append("")
        rows.append(["aa"] + aa)
        rows.append(["ba"] + ba)

        # Anchor rows (two anchor classes)
        for anchor_id, prefix in [("0", "a"), ("2", "b")]:
            xs, ys = extract_anchor_xy(style_metrics, cps, anchor_id)
            rows.append([f"{prefix}x"] + xs)
            rows.append([f"{prefix}y"] + ys)

        # Midpoint rows
        if style_key in ("regular", "semibold"):
            xm = []
            axd = []
            bxd = []
            for cp in cps:
                xm_val = get_mid_x_for_style(style_key, style_metrics, cp, "0")
                xm.append(str(int(xm_val)) if xm_val is not None else "")

                dx_a = compute_dx(style_metrics, cp, "0", style_key)
                dx_b = compute_dx(style_metrics, cp, "2", style_key)

                axd.append(str(int(dx_a)) if dx_a is not None else "")
                bxd.append(str(int(dx_b)) if dx_b is not None else "")

            rows.append(["xm"] + xm)
            rows.append(["axδ"] + axd)
            rows.append(["bxδ"] + bxd)

        else:
            axm = []
            axd = []
            bxm = []
            bxd = []
            for cp in cps:
                axm_val = get_mid_x_for_style(style_key, style_metrics, cp, "0")
                bxm_val = get_mid_x_for_style(style_key, style_metrics, cp, "2")

                axm.append(str(int(axm_val)) if axm_val is not None else "")
                bxm.append(str(int(bxm_val)) if bxm_val is not None else "")

                dx_a = compute_dx(style_metrics, cp, "0", style_key)
                dx_b = compute_dx(style_metrics, cp, "2", style_key)

                axd.append(str(int(dx_a)) if dx_a is not None else "")
                bxd.append(str(int(dx_b)) if dx_b is not None else "")

            rows.append(["axm"] + axm)
            rows.append(["axδ"] + axd)
            rows.append(["bxm"] + bxm)
            rows.append(["bxδ"] + bxd)

    return texify(rows)


# ----------------------------------------------------------------------
# Marks table (kept separate, minimal shared helpers)
# ----------------------------------------------------------------------

def make_fontmetrics_table_for_marks(marks: list[str], anchor_id: str) -> str:
    cps = [ord(cp) for cp in marks]
    all_metrics = load_all_fontmetrics()

    rows = []

    # Header rows
    rows.extend(build_header_rows(cps))

    prefix = "a" if anchor_id == "0" else "b"

    for style_key in STYLE_KEYS:
        style_label = STYLE_LABELS[style_key]
        style_metrics = all_metrics[style_key]

        # Glyph row (no CGJ)
        glyphs = []
        for cp in cps:
            raw = f'\\char"{cp:04X}'
            glyphs.append(apply_style(style_key, raw))
        rows.append([style_label] + glyphs)

        # Anchor rows (one anchor class)
        xs, ys = extract_anchor_xy(style_metrics, cps, anchor_id)
        rows.append([f"{prefix}x"] + xs)
        rows.append([f"{prefix}y"] + ys)

        # Upright midpoint + delta
        xm = []
        dx = []
        for cp in cps:
            xm_val = get_upright_mid_x(style_metrics, cp)
            xm.append(str(int(xm_val)) if xm_val is not None else "")

            anchor = get_anchor(style_metrics, cp, anchor_id)
            if anchor and xm_val is not None:
                delta = anchor[0] - xm_val
                dx.append(str(int(delta)))
            else:
                dx.append("")

        rows.append(["xm"] + xm)
        rows.append([f"{prefix}xδ"] + dx)

    return texify(rows)


# ----------------------------------------------------------------------
# LaTeX wrapper (unchanged)
# ----------------------------------------------------------------------

from string import Template

def wrap_in_table_environment(table_body: str, caption: str, label: str) -> str:
    try:
        first_row = table_body.strip().split("\\\\")[0]
        cols = first_row.count("&") + 1
    except Exception:
        cols = 1

    colspec = "l" + ("r" * (cols - 1))

    template = Template(
        r"""
\begin{table}[htbp]
\captionsetup{justification=raggedright, singlelinecheck=false}
\caption{$caption}
\label{$label}
\setlength{\tabcolsep}{1pt}

{\small
\begin{tabular}{$colspec}
$table_body
\end{tabular}
}
\end{table}
"""
    )

    return template.substitute(
        caption=caption,
        label=label,
        colspec=colspec,
        table_body=table_body,
    )
