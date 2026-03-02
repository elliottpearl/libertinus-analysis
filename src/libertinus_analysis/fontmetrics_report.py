# fontmetrics_report.py

from __future__ import annotations

from .fontmetrics_loader import (
    load_all_fontmetrics,
    get_anchor,
)
from .fontmetrics_helpers import (
    get_bbox_mid_x,
    compute_dx,
)
from .tex_helpers import (
    latex_font_style,
)


# ----------------------------------------------------------------------
# Table construction
# ----------------------------------------------------------------------

def make_fontmetrics_table(bases: list[str]) -> str:
    """
    Build the LaTeX table body (no wrapper).
    bases: list of characters, e.g. ['a','b','c',...]
    """

    # Convert characters → integer codepoints
    cps = [ord(ch) for ch in bases]

    # Load all styles
    all_metrics = load_all_fontmetrics()

    rows = []

    # ------------------------------------------------------------
    # Header row: hex codepoints
    # ------------------------------------------------------------
    header_hex = "hex & " + " & ".join(f"{cp:04X}" for cp in cps)
    rows.append(header_hex)

    # ------------------------------------------------------------
    # Full blocks for all four styles
    # ------------------------------------------------------------
    for style_key, style_header in [
        ("regular", "reg"),
        ("italic", "it"),
        ("semibold", "sb"),
        ("semibold_italic", "si"),
    ]:
        style_metrics = all_metrics[style_key]

        # --------------------------------------------------------
        # Style glyph row
        # --------------------------------------------------------
        styled_cells = []
        for cp in cps:
            raw = (
                f'\\char"{cp:04X} '
                f'\\char"{cp:04X}\\char"0307 '
                f'\\char"{cp:04X}\\char"0331'
            )
            if style_key == "regular":
                # regular block uses unwrapped glyphs
                styled_cells.append(raw)
            else:
                styled_cells.append(latex_font_style(style_key, raw))

        rows.append(style_header + " & " + " & ".join(styled_cells))

        # --------------------------------------------------------
        # Anchor rows: ax, ay (anchor 0), bx, by (anchor 2)
        # --------------------------------------------------------
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

        # --------------------------------------------------------
        # BBox midpoint row (□xm → \char"25A1 xm)
        # --------------------------------------------------------
        bbxm = []
        for cp in cps:
            mid = get_bbox_mid_x(style_metrics, cp)
            bbxm.append(str(int(mid)) if mid is not None else "")
        rows.append(r'\char"25A1 xm & ' + " & ".join(bbxm))

        # --------------------------------------------------------
        # dx_center and dx_norm for anchor 0 (axδ, ax%)
        # --------------------------------------------------------
        axd = []   # axδ
        axp = []   # ax%
        for cp in cps:
            dx, dx_norm = compute_dx(style_metrics, cp, "0")
            axd.append(str(int(dx)) if dx is not None else "")
            axp.append(f"{dx_norm:.2f}" if dx_norm is not None else "")
        rows.append("axδ & " + " & ".join(axd))
        rows.append("ax\\% & " + " & ".join(axp))

        # --------------------------------------------------------
        # dx_center and dx_norm for anchor 2 (bxδ, bx%)
        # --------------------------------------------------------
        bxd = []   # bxδ
        bxp = []   # bx%
        for cp in cps:
            dx, dx_norm = compute_dx(style_metrics, cp, "2")
            bxd.append(str(int(dx)) if dx is not None else "")
            bxp.append(f"{dx_norm:.2f}" if dx_norm is not None else "")
        rows.append("bxδ & " + " & ".join(bxd))
        rows.append("bx\\% & " + " & ".join(bxp))

    # ------------------------------------------------------------
    # Join rows into LaTeX table body
    # ------------------------------------------------------------
    body = " \\\\\n".join(rows) + " \\\\\n"
    return body


# ----------------------------------------------------------------------
# LaTeX wrapper
# ----------------------------------------------------------------------

def wrap_in_table_environment(table_body: str, caption: str, label: str) -> str:
    """
    Wrap the table body in a full LaTeX table environment.
    """
    return f"""
\\begin{{table}}[htbp]
\\captionsetup{{justification=raggedright, singlelinecheck=false}}
\\caption{{{caption}}}
\\label{{{label}}}
\\setlength{{\\tabcolsep}}{{1pt}}

{{\\small
\\begin{{tabular}}{{l{'r' * (table_body.count('&') // table_body.count('\\\\'))}}}
{table_body}
\\end{{tabular}}
}}
\\end{{table}}
"""
