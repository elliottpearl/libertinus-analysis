# report_fontmetrics.py
#
# Generate LaTeX tables summarizing fontmetrics data.

from __future__ import annotations

from .fontmetrics_loader import (
    load_all_fontmetrics,
    get_anchor,
    get_bbox_x_mid,
)
from .tex_helpers import tex   # your existing \char"XXXX helper


# ----------------------------------------------------------------------
# Row definitions
# ----------------------------------------------------------------------

def build_rows_for_style(style: str, codepoints: list[str], metrics: dict) -> list[str]:
    """
    Build the 5 LaTeX table rows for a single style.
    Returns a list of strings, each representing one LaTeX row.
    """

    rows = []

    # 1. anchor_0_x
    vals = []
    for cp in codepoints:
        anchor = get_anchor(metrics[style], cp, "0")
        vals.append(str(anchor[0]) if anchor else "")
    rows.append(" & ".join(vals) + " \\\\")

    # 2. anchor_0_y
    vals = []
    for cp in codepoints:
        anchor = get_anchor(metrics[style], cp, "0")
        vals.append(str(anchor[1]) if anchor else "")
    rows.append(" & ".join(vals) + " \\\\")

    # 3. anchor_2_x
    vals = []
    for cp in codepoints:
        anchor = get_anchor(metrics[style], cp, "2")
        vals.append(str(anchor[0]) if anchor else "")
    rows.append(" & ".join(vals) + " \\\\")

    # 4. anchor_2_y
    vals = []
    for cp in codepoints:
        anchor = get_anchor(metrics[style], cp, "2")
        vals.append(str(anchor[1]) if anchor else "")
    rows.append(" & ".join(vals) + " \\\\")

    # 5. bbox_x_mid
    vals = []
    for cp in codepoints:
        mid = get_bbox_x_mid(metrics[style], cp)
        vals.append(str(mid) if mid is not None else "")
    rows.append(" & ".join(vals) + " \\\\")

    return rows


# ----------------------------------------------------------------------
# Table assembly
# ----------------------------------------------------------------------

def make_fontmetrics_table(codepoints: list[str], bases: list[str]) -> str:
    """
    Build a complete LaTeX table body (without the outer table environment).

    Includes:
      Row 1: printable glyphs via \\char"XXXX
      Row 2: raw hex codepoints (XXXX)
    """

    metrics = load_all_fontmetrics()

    # Row 1: printable glyphs
    row_glyphs = " & ".join(tex(int(cp, 16)) for cp in codepoints) + " \\\\"

    # Row 2: raw hex (strip "0x")
    row_hex = " & ".join(cp[2:] for cp in codepoints) + " \\\\"

    all_rows = [row_glyphs, row_hex]

    # Metric rows for each style
    for style in ["regular", "italic", "semibold", "semibold_italic"]:
        rows = build_rows_for_style(style, codepoints, metrics)
        all_rows.extend(rows)

    return "\n".join(all_rows)


# ----------------------------------------------------------------------
# LaTeX wrapper
# ----------------------------------------------------------------------

def wrap_in_table_environment(content: str, caption: str = "Glyph metrics") -> str:
    """
    Wrap the table body in a LaTeX table environment.
    Uses .format() to avoid f-string brace escaping issues.
    """

    # Count columns from the first row
    first_row = content.splitlines()[0]
    num_cols = len(first_row.split("&"))
    spec = "r" * num_cols

    template = r"""
\begin{{table}}[htbp]
\captionsetup{{justification=raggedright, singlelinecheck=false}}
\caption{{{caption}}}
\label{{table:fontmetrics}}
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
        spec=spec,
        content=content,
    )