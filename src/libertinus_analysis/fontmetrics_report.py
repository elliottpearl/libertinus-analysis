# fontmetrics_report.py
from __future__ import annotations

from functools import lru_cache

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

# Tags of the a! and b! rows for patched anchors owned by neither the designer
# (unmoved), the heuristic nor a curator; see PROVENANCE_DIR in font_patching.py.
OWNER_TAGS = {"normalized": "n", "derived": "i", "precomposed": "i",
              "designer": "d", "heuristic": "h"}


@lru_cache(maxsize=None)
def patch_owners(style_key: str) -> dict:
    """{codepoint: {class: (owner, (x, y))}} of the base anchors of the patched font."""
    import json
    from fontTools.ttLib import TTFont
    from .font_context import FONTS
    from .font_patching import PROVENANCE_DIR, _base_anchors

    owners = json.loads((PROVENANCE_DIR / f"{style_key}.json").read_text(encoding="utf-8"))
    meta = FONTS[f"{style_key}_patch"]
    ttfont = TTFont(meta["path"])
    anchors = _base_anchors(ttfont, meta["lookup_index"])
    result = {}
    for cp, glyph in ttfont.getBestCmap().items():
        for (g, cls), xy in ((k, v) for k, v in anchors.items() if k[0] == glyph):
            result.setdefault(cp, {})[cls] = (owners.get(glyph, {}).get(str(cls), "?"), xy)
    return result


def bold(cell: str) -> str:
    return f"\\textbf{{{cell}}}" if cell else cell


def make_fontmetrics_table(bases: list[str]) -> str:
    """
    One column per base; per style a block of rows: glyph samples in the
    original and patched fonts, the ideal bounding box, then for the above (a)
    and below (b) anchor the original font's anchor, the candidate (?), anchor
    minus candidate (delta), and the patched anchor where a curator or a later
    stage set it (!). Cells hold "X, Y". The owner of the patched anchor is
    shown in bold: the a/b cell if it is the designer's anchor, the ? cell if it
    is the candidate, the ! cell if it is curated or set by the stem-axis rule.
    A designer anchor whose Y stage 5 moved to the candidate's reference has its
    X bolded in a/b and its Y in ?; one snapped (by up to 5) to another
    reference is bolded whole. Any other patched anchor (inherited, or one that
    neither cell shows) is in the ! row with a tag (OWNER_TAGS).
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
        owners = patch_owners(style_key)

        rows.append(["\\hline " + style_label + SAMPLE_STRUT] + [sample_letter_glyph(cp, style_key) for cp in cps])
        rows.append(["patch" + SAMPLE_STRUT] + [sample_letter_glyph(cp, f"{style_key}_patch") for cp in cps])

        anchor_rows = {}
        ideals = {}
        for anchor_id, prefix in [("0", "a"), ("2", "b")]:
            have, want, delta, ideal, final = [], [], [], [], []
            for cp in cps:
                anchor = get_anchor(style_metrics, cp, anchor_id)
                cand = get_anchor_candidate(style_key, style_metrics, cp, anchor_id)
                have_cell = xy_cell(*anchor) if anchor else ""
                want_cell = xy_cell(cand[0], cand[1]) if cand else ""
                final_cell = ""
                owner, xy = owners.get(cp, {}).get(int(anchor_id), (None, None))
                if owner == "designer" and have_cell == xy_cell(*xy):
                    have_cell = bold(have_cell)
                elif owner == "heuristic" and want_cell == xy_cell(*xy):
                    want_cell = bold(want_cell)
                elif owner in ("curated", "stem"):
                    final_cell = bold(xy_cell(*xy))
                elif (owner == "normalized" and anchor and cand
                      and round(anchor[0]) == xy[0] and round(cand[1]) == xy[1]):
                    # stage 5 moved Y only: the designer's X, the candidate's Y (its reference)
                    have_cell = f"{bold(str(round(anchor[0])))}, {round(anchor[1])}"
                    want_cell = f"{round(cand[0])}, {bold(str(round(cand[1])))}"
                elif owner == "normalized" and anchor and round(anchor[0]) == xy[0]:
                    # stage 5 snapped Y by up to 5 units to a reference other than the candidate's
                    have_cell = bold(have_cell)
                elif owner is not None:
                    final_cell = f"{xy_cell(*xy)}\\textsuperscript{{{OWNER_TAGS.get(owner, '?')}}}"
                have.append(have_cell)
                want.append(want_cell)
                final.append(final_cell)
                ideal.append(cand[2] if cand else "")
                if anchor and cand:
                    delta.append(xy_cell(anchor[0] - cand[0], anchor[1] - cand[1]))
                else:
                    delta.append("")
            anchor_rows[prefix] = (have, want, delta, final)
            ideals[prefix] = ideal

        ideal = [f"{t}, {b}" if t and b else "" for t, b in zip(ideals["a"], ideals["b"])]
        rows.append(["ideal"] + ideal)

        for prefix in ("a", "b"):
            have, want, delta, final = anchor_rows[prefix]
            rows.append([prefix] + have)
            rows.append([f"{prefix}?"] + want)
            rows.append([f"{prefix}$\\delta$"] + delta)
            rows.append([f"{prefix}!"] + final)

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
    status = {cp: {"inherited": False, "other": False} for cp in cps}
    for style_key in STYLE_KEYS:
        owners = patch_owners(style_key)
        for cp in cps:
            for cls in (0, 2):
                if cls in owners.get(cp, {}):
                    owner = owners[cp][cls][0]
                    status[cp]["inherited" if owner in ("derived", "precomposed") else "other"] = True
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
