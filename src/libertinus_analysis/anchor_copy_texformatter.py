# anchor_copy_texformatter.py
"""
Format copied-anchor cluster analysis into a LaTeX fragment.

Used by run_anchor_copy_report.py to write tex/input/copied_anchors.tex.
"""

from __future__ import annotations


def tex_escape(s: str) -> str:
    """Escape TeX special characters."""
    return (
        s.replace("&", "\\&")
         .replace("%", "\\%")
         .replace("#", "\\#")
    )


# Marks used to visualize above/below anchor positions
ABOVE_MARKS = ["0307", "030C", "0302"]   # dot, caron, circumflex
BELOW_MARKS = ["0323", "032C", "0331"]   # dot below, caron below, macron below


def format_cluster_row(pair, cps, marks):
    """
    pair = (x, y)
    cps = list of codepoints
    marks = list of combining mark hex strings
    """
    ax, ay = pair
    parts = []

    for cp in cps:
        for mk in marks:
            parts.append(f'\\char"{cp:04X}\\cgj\\char"{mk}')

    joined = " ".join(parts)
    return f"({ax}, {ay}) {joined}"


def format_style_section(style_key: str, clusters: list, above=True):
    """
    style_key: "regular", "italic", "semibold", "semibolditalic"
    clusters: list of (pair, cps)
    above: True → above anchors, False → below anchors
    """

    title = f"{style_key.capitalize()}, {'above' if above else 'below'}"
    lines = [f"\\section*{{{tex_escape(title)}}}", ""]

    marks = ABOVE_MARKS if above else BELOW_MARKS

    if not clusters:
        lines.append("\\emph{No clusters detected.}")
        return "\n".join(lines)

    for pair, cps in clusters:
        row = format_cluster_row(pair, cps, marks)
        lines.append(row)
        lines.append("")  # blank line between rows

    return "\n".join(lines)


def format_all_styles_tex(results: dict):
    """
    results = {
        "regular": {"above": [...], "below": [...]},
        "italic": {...},
        "semibold": {...},
        "semibolditalic": {...},
    }

    Returns a LaTeX fragment containing all six sections.
    """

    order = ["regular", "italic", "semibold", "semibolditalic"]
    tex_sections = []

    for style in order:
        style_res = results.get(style, {})
        tex_sections.append(
            format_style_section(style, style_res.get("above", []), above=True)
        )
        tex_sections.append("")
        tex_sections.append(
            format_style_section(style, style_res.get("below", []), above=False)
        )
        tex_sections.append("")

    return "\n".join(tex_sections)
