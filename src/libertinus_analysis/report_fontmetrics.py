# report_fontmetrics.py
#
# Generate LaTeX tables summarizing fontmetrics data.

from __future__ import annotations

from .fontmetrics_loader import (
    load_all_fontmetrics,
    get_anchor,
)
from .tex_helpers import tex, latex_font_style


# ----------------------------------------------------------------------
# Glyph demo builder
# ----------------------------------------------------------------------

DEMO_ABOVE = 0x0307   # U+0307 COMBINING DOT ABOVE
DEMO_BELOW = 0x0331   # U+0331 COMBINING MACRON BELOW


def glyph_demo_sequence(cp: int) -> str:
    base = tex(cp)
    above = tex(cp) + tex(DEMO_ABOVE)
    below = tex(cp) + tex(DEMO_BELOW)
    return f"{base} {above} {below}"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def fmt_num(x):
    if x is None:
        return ""
    if abs(x - int(x)) < 1e-6:
        return str(int(x))
    if abs(x) < 10:
        return f"{x:.2f}"
    return f"{x:.1f}"


def get_bbox(style_metrics, cp):
    glyphs = style_metrics.get("glyphs", {})
    entry = glyphs.get(cp)
    if not entry:
        return None
    return entry.get("bbox")


def get_outline_center_and_width(style_metrics, cp):
    bbox = get_bbox(style_metrics, cp)
    if not bbox:
        return None, None
    xmin, ymin, xmax, ymax = bbox
    center = (xmin + xmax) / 2
    width = xmax - xmin
    return center, width


def build_anchor_row(style, codepoints, metrics, anchor_id, coord):
    vals = []
    for cp in codepoints:
        anchor = get_anchor(metrics[style], cp, anchor_id)
        vals.append(str(anchor[coord]) if anchor else "")
    return " & ".join(vals) + " \\\\"


def build_bbox_mid_row(style, codepoints, metrics):
    vals = []
    for cp in codepoints:
        bbox = get_bbox(metrics[style], cp)
        if bbox:
            xmin, ymin, xmax, ymax = bbox
            mid = (xmin + xmax) // 2
            vals.append(str(mid))
        else:
            vals.append("")
    return " & ".join(vals) + " \\\\"


# ----------------------------------------------------------------------
# New dx rows
# ----------------------------------------------------------------------

def build_dx_rows(style, codepoints, metrics, anchor_id):
    """
    Build dx_center and dx_norm rows for either above ("0") or below ("2").
    """
    dx_center_vals = []
    dx_norm_vals = []

    for cp in codepoints:
        anchor = get_anchor(metrics[style], cp, anchor_id)
        center, width = get_outline_center_and_width(metrics[style], cp)

        if not anchor or center is None or not width:
            dx_center_vals.append("")
            dx_norm_vals.append("")
            continue

        ax = anchor[0]
        dx = ax - center
        dx_center_vals.append(fmt_num(dx))

        dx_norm = dx / width if width != 0 else 0
        dx_norm_vals.append(fmt_num(dx_norm))

    return (
        " & ".join(dx_center_vals) + " \\\\",
        " & ".join(dx_norm_vals) + " \\\\",
    )


# ----------------------------------------------------------------------
# Table assembly
# ----------------------------------------------------------------------

def make_fontmetrics_table(codepoints: list[str], bases: list[str]) -> str:
    metrics = load_all_fontmetrics()
    cps_int = [int(cp, 16) for cp in codepoints]

    # Row 1: hex
    row_hex = " & ".join(f"{cp:04X}" for cp in cps_int) + " \\\\"

    # Row 2: regular glyph demo
    row_regular_demo = " & ".join(
        latex_font_style("regular", glyph_demo_sequence(cp))
        for cp in cps_int
    ) + " \\\\"

    all_rows = [row_hex, row_regular_demo]

    # Regular metrics
    style = "regular"
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 0))  # above_x
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 1))  # above_y
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 0))  # below_x
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 1))  # below_y
    all_rows.append(build_bbox_mid_row(style, codepoints, metrics))        # bbox_x_mid

    # New dx rows (regular)
    dx_above_center, dx_above_norm = build_dx_rows(style, codepoints, metrics, "0")
    dx_below_center, dx_below_norm = build_dx_rows(style, codepoints, metrics, "2")
    all_rows.extend([dx_above_center, dx_above_norm, dx_below_center, dx_below_norm])

    # Italic glyph demo
    row_italic_demo = " & ".join(
        latex_font_style("italic", glyph_demo_sequence(cp))
        for cp in cps_int
    ) + " \\\\"
    all_rows.append(row_italic_demo)

    # Italic metrics
    style = "italic"
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 0))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 1))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 0))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 1))
    all_rows.append(build_bbox_mid_row(style, codepoints, metrics))

    dx_above_center, dx_above_norm = build_dx_rows(style, codepoints, metrics, "0")
    dx_below_center, dx_below_norm = build_dx_rows(style, codepoints, metrics, "2")
    all_rows.extend([dx_above_center, dx_above_norm, dx_below_center, dx_below_norm])

    # Semibold glyph demo
    row_semibold_demo = " & ".join(
        latex_font_style("semibold", glyph_demo_sequence(cp))
        for cp in cps_int
    ) + " \\\\"
    all_rows.append(row_semibold_demo)

    # Semibold metrics
    style = "semibold"
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 0))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 1))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 0))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 1))
    all_rows.append(build_bbox_mid_row(style, codepoints, metrics))

    dx_above_center, dx_above_norm = build_dx_rows(style, codepoints, metrics, "0")
    dx_below_center, dx_below_norm = build_dx_rows(style, codepoints, metrics, "2")
    all_rows.extend([dx_above_center, dx_above_norm, dx_below_center, dx_below_norm])

    # Semibold italic glyph demo
    row_semibold_italic_demo = " & ".join(
        latex_font_style("semibold_italic", glyph_demo_sequence(cp))
        for cp in cps_int
    ) + " \\\\"
    all_rows.append(row_semibold_italic_demo)

    # Semibold italic metrics
    style = "semibold_italic"
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 0))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "0", 1))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 0))
    all_rows.append(build_anchor_row(style, codepoints, metrics, "2", 1))
    all_rows.append(build_bbox_mid_row(style, codepoints, metrics))

    dx_above_center, dx_above_norm = build_dx_rows(style, codepoints, metrics, "0")
    dx_below_center, dx_below_norm = build_dx_rows(style, codepoints, metrics, "2")
    all_rows.extend([dx_above_center, dx_above_norm, dx_below_center, dx_below_norm])

    return "\n".join(all_rows)


# ----------------------------------------------------------------------
# LaTeX wrapper
# ----------------------------------------------------------------------

def wrap_in_table_environment(content: str,
                              caption: str = "Glyph metrics",
                              label: str = "table:fontmetrics") -> str:
    first_row = content.splitlines()[0]
    num_cols = len(first_row.split("&"))
    spec = "r" * num_cols

    template = r"""
\begin{{table}}[htbp]
\captionsetup{{justification=raggedright, singlelinecheck=false}}
\caption{{{caption}}}
\label{{{label}}}
\setlength{{\tabcolsep}}{{1pt}}

{{\small
\begin{{tabular}}{{{spec}}}
{content}
\end{{tabular}}
}}
\end{{table}}
"""

    return template.format(
        caption=caption,
        label=label,
        spec=spec,
        content=content,
    )
    