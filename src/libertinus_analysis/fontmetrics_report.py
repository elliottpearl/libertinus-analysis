# fontmetrics_report.py
from __future__ import annotations

from .fontmetrics_loader import (
    load_all_fontmetrics,
    get_anchor,
)
from .fontmetrics_helpers import (
    get_mid_x_for_style,
    compute_dx,
    get_upright_mid_x,
)
from .tex_helpers import (
    latex_font_style,
)


# ----------------------------------------------------------------------
# Table construction
# ----------------------------------------------------------------------

def _sample_cells_for_style(style_key: str, cps: list[int]) -> list[str]:
    """
    Build the sample glyph cells for a given style, inserting CGJ
    to force use of anchors rather than precomposed glyphs.
    """
    cells = []
    for cp in cps:
        raw = (
            f'\\char"{cp:04X} '
            f'\\char"{cp:04X}\\cgj\\char"0307 '
            f'\\char"{cp:04X}\\cgj\\char"0331'
        )
        if style_key == "regular":
            cells.append(raw)
        else:
            cells.append(latex_font_style(style_key, raw))
    return cells


def make_fontmetrics_table(bases: list[str]) -> str:
    """
    Build the LaTeX table body (no wrapper).
    bases: list of characters, e.g. ['a','b','c',...]
    """

    cps = [ord(ch) for ch in bases]
    all_metrics = load_all_fontmetrics()
    rows = []

    # Header row: hex codepoints
    header_hex = "hex & " + " & ".join(f"{cp:04X}" for cp in cps)
    rows.append(header_hex)

    # Full blocks for all four styles
    for style_key, style_header in [
        ("regular", "reg"),
        ("italic", "it"),
        ("semibold", "sb"),
        ("semibold_italic", "si"),
    ]:
        style_metrics = all_metrics[style_key]

        # Style glyph row (with CGJ)
        styled_cells = _sample_cells_for_style(style_key, cps)
        rows.append(style_header + " & " + " & ".join(styled_cells))

        # Anchor rows: ax, ay (anchor 0), bx, by (anchor 2)
        for anchor_id, prefix in [("0", "a"), ("2", "b")]:
            xs = []
            ys = []
            for cp in cps:
                anchor = get_anchor(style_metrics, cp, anchor_id)
                if anchor:
                    xs.append(str(int(anchor[0])))
                    ys.append(str(int(anchor[1])))
                else:
                    xs.append("")
                    ys.append("")
            rows.append(f"{prefix}x & " + " & ".join(xs))
            rows.append(f"{prefix}y & " + " & ".join(ys))

        # Midpoint and deltas
        if style_key in ("regular", "semibold"):
            # Upright: single xm, axδ, bxδ
            xm_cells = []
            axd_cells = []
            bxd_cells = []
            for cp in cps:
                xm = get_mid_x_for_style(style_key, style_metrics, cp, "0")
                xm_cells.append(str(int(xm)) if xm is not None else "")

                dx_a = compute_dx(style_metrics, cp, "0", style_key)
                axd_cells.append(str(int(dx_a)) if dx_a is not None else "")

                dx_b = compute_dx(style_metrics, cp, "2", style_key)
                bxd_cells.append(str(int(dx_b)) if dx_b is not None else "")

            rows.append("xm & " + " & ".join(xm_cells))
            rows.append("axδ & " + " & ".join(axd_cells))
            rows.append("bxδ & " + " & ".join(bxd_cells))

        else:
            # Italic / semibold_italic: axm, axδ, bxm, bxδ
            axm_cells = []
            axd_cells = []
            bxm_cells = []
            bxd_cells = []
            for cp in cps:
                axm = get_mid_x_for_style(style_key, style_metrics, cp, "0")
                bxm = get_mid_x_for_style(style_key, style_metrics, cp, "2")

                axm_cells.append(str(int(axm)) if axm is not None else "")
                bxm_cells.append(str(int(bxm)) if bxm is not None else "")

                dx_a = compute_dx(style_metrics, cp, "0", style_key)
                dx_b = compute_dx(style_metrics, cp, "2", style_key)

                axd_cells.append(str(int(dx_a)) if dx_a is not None else "")
                bxd_cells.append(str(int(dx_b)) if dx_b is not None else "")

            rows.append("axm & " + " & ".join(axm_cells))
            rows.append("axδ & " + " & ".join(axd_cells))
            rows.append("bxm & " + " & ".join(bxm_cells))
            rows.append("bxδ & " + " & ".join(bxd_cells))

    body = " \\\\\n".join(rows) + " \\\\\n"
    return body


# ----------------------------------------------------------------------
# LaTeX wrapper
# ----------------------------------------------------------------------

from string import Template

def wrap_in_table_environment(table_body: str, caption: str, label: str) -> str:
    """
    Wrap the table body in a full LaTeX table environment.
    """

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


def make_fontmetrics_table_for_marks(marks: list[str], anchor_id: str) -> str:
    """
    Build a LaTeX table for combining marks.
    All marks in `marks` are assumed to use the same anchor class:
        anchor_id = "0" (above) or "2" (below)

    For marks:
        - use bbox midpoint (upright) as xm
        - delete percentage rows
        - do not apply italic slant midpoint
    """

    cps = [ord(ch) for ch in marks]
    all_metrics = load_all_fontmetrics()
    rows = []

    # Header
    header_hex = "hex & " + " & ".join(f"{cp:04X}" for cp in cps)
    rows.append(header_hex)

    # Iterate over styles
    for style_key, style_header in [
        ("regular", "reg"),
        ("italic", "it"),
        ("semibold", "sb"),
        ("semibold_italic", "si"),
    ]:
        style_metrics = all_metrics[style_key]

        # Rendered glyph row (with CGJ)
        styled_cells = []
        for cp in cps:
            raw = f'\\char"{cp:04X}'
            if style_key == "regular":
                styled_cells.append(raw)
            else:
                styled_cells.append(latex_font_style(style_key, raw))
        rows.append(style_header + " & " + " & ".join(styled_cells))

        # Anchor rows (only one anchor class)
        prefix = "a" if anchor_id == "0" else "b"

        xs = []
        ys = []
        for cp in cps:
            anchor = get_anchor(style_metrics, cp, anchor_id)
            if anchor:
                xs.append(str(int(anchor[0])))
                ys.append(str(int(anchor[1])))
            else:
                xs.append("")
                ys.append("")
        rows.append(f"{prefix}x & " + " & ".join(xs))
        rows.append(f"{prefix}y & " + " & ".join(ys))

        # BBox midpoint (upright only for marks)
        xm_cells = []
        delta_cells = []
        for cp in cps:
            xm = get_upright_mid_x(style_metrics, cp)
            xm_cells.append(str(int(xm)) if xm is not None else "")

            dx = None
            anchor = get_anchor(style_metrics, cp, anchor_id)
            if anchor and xm is not None:
                dx = anchor[0] - xm
            delta_cells.append(str(int(dx)) if dx is not None else "")

        rows.append("xm & " + " & ".join(xm_cells))
        rows.append(f"{prefix}xδ & " + " & ".join(delta_cells))

    return " \\\\\n".join(rows) + " \\\\\n"
