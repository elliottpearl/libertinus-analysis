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
    # Regular glyph row (rendered)
    # ------------------------------------------------------------
    row_reg = "reg & " + " & ".join(
        f'\\char"{cp:04X} \\char"{cp:04X}\\char"0307 \\char"{cp:04X}\\char"0331'
        for cp in cps
    )
    rows.append(row_reg)

    # ------------------------------------------------------------
    # For each style: regular, italic, semibold, semibold_italic
    # ------------------------------------------------------------
    for style_key in ["regular", "italic", "semibold", "semibold_italic"]:
        style_metrics = all_metrics[style_key]

        # Style label row header
        if style_key == "regular":
            style_header = "reg"
            style_label = ""
        elif style_key == "italic":
            style_header = "it"
            style_label = r"\itshape "
        elif style_key == "semibold":
            style_header = "sb"
            style_label = ""
        else:  # semibold_italic
            style_header = "si"
            style_label = r"\itshape "

        # Style glyph row
        row_style = style_header + " & " + " & ".join(
            f'{style_label}\\char"{cp:04X} '
            f'{style_label}\\char"{cp:04X}\\char"0307 '
            f'{style_label}\\char"{cp:04X}\\char"0331'
            for cp in cps
        )
        rows.append(row_style)

        # --------------------------------------------------------
        # Anchor rows: r0x, r0y, r2x, r2y
        # --------------------------------------------------------
        for anchor_id, prefix in [("0", "r0"), ("2", "r2")]:
            xs = []
            ys = []
            for cp in cps:
                anchor = get_anchor(style_metrics, cp, anchor_id)
                if anchor:
                    xs.append(str(anchor[0]))
                    ys.append(str(anchor[1]))
                else:
                    xs.append("")
                    ys.append("")
            rows.append(f"{prefix}x & " + " & ".join(xs))
            rows.append(f"{prefix}y & " + " & ".join(ys))

        # --------------------------------------------------------
        # BBox midpoint row (rbx)
        # --------------------------------------------------------
        rbx = []
        for cp in cps:
            mid = get_bbox_mid_x(style_metrics, cp)
            rbx.append(str(mid) if mid is not None else "")
        rows.append("rbx & " + " & ".join(rbx))

        # --------------------------------------------------------
        # dx_center and dx_norm for anchor 0 (rdc, rdn)
        # --------------------------------------------------------
        rdc = []
        rdn = []
        for cp in cps:
            dx, dx_norm = compute_dx(style_metrics, cp, "0")
            rdc.append(f"{dx:.2f}" if dx is not None else "")
            rdn.append(f"{dx_norm:.2f}" if dx_norm is not None else "")
        rows.append("rdc & " + " & ".join(rdc))
        rows.append("rdn & " + " & ".join(rdn))

        # --------------------------------------------------------
        # dx_center and dx_norm for anchor 2 (rbc, rbn)
        # --------------------------------------------------------
        rbc = []
        rbn = []
        for cp in cps:
            dx, dx_norm = compute_dx(style_metrics, cp, "2")
            rbc.append(f"{dx:.2f}" if dx is not None else "")
            rbn.append(f"{dx_norm:.2f}" if dx_norm is not None else "")
        rows.append("rbc & " + " & ".join(rbc))
        rows.append("rbn & " + " & ".join(rbn))

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
