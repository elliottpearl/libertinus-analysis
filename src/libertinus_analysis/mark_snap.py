"""
Mark snap candidates: a test of moving mark anchors X onto the mark-anchor model.

For each above/below mark anchor in a patched font, the target is

    X = C + Y tan(theta) + d - K

C is where the mark's slanted axis meets the baseline (centre of the de-slanted
outline), Y the mark anchor's own height, K the style's shift (150 above, -12
below in semibold italic; 0 elsewhere), and d the mark's offset from its axis in
patched regular (X - C there), so an asymmetric mark keeps regular's offset.
Regular defines d, so it has no candidates; marks with no glyph in regular have
no d and are listed but not moved.

A mark whose anchor is more than SNAP_TOLERANCE from its target is a candidate.
Each style gets a test font (fonts/*-marksnap.otf): the patched font with only
the candidates' X changed. The sheet tex/input/mark_snap.tex sets every Latin and
IPA base that has an anchor in the mark's class with the mark, patched font then
test font, so the move can be judged by eye. Nothing here changes the patch.
"""

from __future__ import annotations

import re

from fontTools.ttLib import TTFont

from data.ipa.ipa_unicode import unicode_groups

from .config import ROOT, TEX_INPUT_DIR
from .font_context import FONTS
from .font_patching_anchors import load_human_anchors
from .fontmetrics_extractor import get_axis_x
from .fontmetrics_helpers import SHIFT_K, SLOPE
from .tex_helpers import latex_font_style

SNAP_TOLERANCE = 5
STYLES = ["italic", "semibold", "semibold_italic"]
STYLE_TITLES = {"italic": "Italic", "semibold": "Semibold", "semibold_italic": "Semibold italic"}
ABOVE, BELOW = 0, 2
SIDE = {ABOVE: "above", BELOW: "below"}
SCOPE = sorted(set(unicode_groups["BASE_LATIN"]["items"]) | set(unicode_groups["BASE_IPA"]["items"]))

# ----------------------------------------------------------------------
# Font data
# ----------------------------------------------------------------------

def _lookup(font, font_key):
    return font["GPOS"].table.LookupList.Lookup[FONTS[font_key]["lookup_index"]]


def _mark_anchors(font, font_key):
    """glyph -> (class, [anchor records]) for every above/below mark anchor."""
    marks = {}
    for sub in _lookup(font, font_key).SubTable:
        for glyph, rec in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
            if rec.Class in (ABOVE, BELOW) and rec.MarkAnchor is not None:
                marks.setdefault(glyph, (rec.Class, []))[1].append(rec.MarkAnchor)
    return marks


def _base_anchor_glyphs(font, font_key):
    """class -> set of base glyphs with an anchor in that class."""
    out = {ABOVE: set(), BELOW: set()}
    for sub in _lookup(font, font_key).SubTable:
        for glyph, rec in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
            for cls in (ABOVE, BELOW):
                if cls < len(rec.BaseAnchor) and rec.BaseAnchor[cls] is not None:
                    out[cls].add(glyph)
    return out


def _regular_offsets():
    """glyph -> d = X - C in patched regular."""
    font = TTFont(FONTS["regular_patch"]["path"])
    gs = font.getGlyphSet()
    return {g: anchors[0].XCoordinate - get_axis_x(gs, g, 0.0)
            for g, (cls, anchors) in _mark_anchors(font, "regular_patch").items()}


def _ccmp(style_key):
    """(.cap glyph -> encoded mark glyph, set of @capitals glyphs) from the style's ccmp.fea."""
    text = (ROOT / "data" / "fea" / style_key / "ccmp.fea").read_text(encoding="utf-8")
    text = re.sub(r"#[^\n]*", "", text)
    caps = {cap: src for src, cap in re.findall(r"sub\s+(\S+)\s+by\s+(\S+\.cap)\s*;", text)}
    m = re.search(r"@capitals\s*=\s*\[(.*?)\]\s*;", text, re.S)
    return caps, set(m.group(1).split()) if m else set()


def _curated(style_key, cmap):
    human = load_human_anchors(style_key)
    out = {(cmap[cp], cls) for cp, d in human.get("marks", {}).items() if cp in cmap for cls in d}
    out |= {(g, cls) for g, d in human.get("marks_by_name", {}).items() for cls in d}
    return out

# ----------------------------------------------------------------------
# Candidates
# ----------------------------------------------------------------------

def snap_candidates(style_key, reg_offsets):
    """Return (font, candidates, no_reference) for the patched style."""
    font_key = f"{style_key}_patch"
    font = TTFont(FONTS[font_key]["path"])
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    rev = {}
    for cp, g in sorted(cmap.items()):
        rev.setdefault(g, cp)
    caps, capitals = _ccmp(style_key)
    curated = _curated(style_key, cmap)
    slope = SLOPE[style_key]

    candidates, no_reference = [], []
    for glyph, (cls, anchors) in sorted(_mark_anchors(font, font_key).items()):
        x, y = anchors[0].XCoordinate, anchors[0].YCoordinate
        if glyph not in reg_offsets:
            no_reference.append(glyph)
            continue
        k = SHIFT_K.get(style_key, {}).get(str(cls), 0)
        c = get_axis_x(gs, glyph, slope)
        target = round(c + y * slope + reg_offsets[glyph] - k)
        if abs(target - x) <= SNAP_TOLERANCE:
            continue
        sample = rev.get(caps[glyph]) if glyph in caps else rev.get(glyph)
        candidates.append({
            "glyph": glyph, "cls": cls, "xy": (x, y), "target": target,
            "d": reg_offsets[glyph], "cap": glyph in caps, "sample": sample,
            "curated": (glyph, cls) in curated, "has_cap_form": glyph in caps.values(),
        })
    return font, candidates, no_reference, capitals


def build_snap_font(style_key, font, candidates):
    targets = {c["glyph"]: c["target"] for c in candidates}
    for glyph, (cls, anchors) in _mark_anchors(font, f"{style_key}_patch").items():
        if glyph in targets:
            for anchor in anchors:
                anchor.XCoordinate = targets[glyph]
    font.save(FONTS[f"{style_key}_marksnap"]["path"])

# ----------------------------------------------------------------------
# LaTeX
# ----------------------------------------------------------------------

def _num(v):
    """An integer in math mode with a real minus sign."""
    return f"${round(v)}$"


def _bases(style_key, cand, font, capitals, anchored):
    """Scope bases that show this candidate: with an anchor in its class; capitals only for a .cap
    mark, and no capitals for a mark that ccmp swaps for its .cap form over them."""
    cmap = font.getBestCmap()
    out = []
    for cp in SCOPE:
        g = cmap.get(cp)
        if g is None or g not in anchored[cand["cls"]]:
            continue
        if cand["cap"] and g not in capitals:
            continue
        if cand["has_cap_form"] and g in capitals:
            continue
        out.append(cp)
    return out


def _format_candidate(style_key, cand, bases):
    x, y = cand["xy"]
    mark_moves = x - cand["target"]
    name = f"\\texttt{{\\detokenize{{{cand['glyph']}}}}}"
    code = f"U+{cand['sample']:04X} " if cand["sample"] and not cand["cap"] else ""
    via = f" (over capitals, from U+{cand['sample']:04X})" if cand["cap"] and cand["sample"] else ""
    tag = ", curated" if cand["curated"] else ""
    head = (f"\\subsubsection*{{{code}{name}{via}, {SIDE[cand['cls']]}{tag}}}\n"
            f"Anchor ({_num(x)}, {_num(y)}), target $X$ {_num(cand['target'])} "
            f"($d$ = {_num(cand['d'])}): "
            f"the mark moves {abs(mark_moves)} units {'right' if mark_moves > 0 else 'left'}.")
    if not bases or not cand["sample"]:
        return head + "\n\nNo Latin or IPA base shows this mark.\n"
    pairs = []
    for cp in bases:
        s = f'\\char"{cp:04X}\\cgj\\char"{cand["sample"]:04X}'
        pairs.append(f"\\SnapPair{{{latex_font_style(f'{style_key}_patch', s)}}}"
                     f"{{{latex_font_style(f'{style_key}_marksnap', s)}}}")
    return head + "\n\n{\\raggedright\\lineskip=6pt\n" + "\n".join(pairs) + "\\par}\n"


HEADER = r"""% Generated by mark_snap.py (run_mark_snap_sheet.py). Do not edit.
\providecommand{\SnapPair}[2]{\mbox{#1\,{\color{snapcolor}#2}}\hspace{3mm plus 1mm}\allowbreak}
"""


def format_sheet(results):
    parts = [HEADER]
    rows = []
    for style in STYLES:
        cands = results[style]["candidates"]
        n = {cls: sum(c["cls"] == cls for c in cands) for cls in (ABOVE, BELOW)}
        rows.append(f"{STYLE_TITLES[style]} & {n[ABOVE]} & {n[BELOW]} & "
                    f"{sum(c['curated'] for c in cands)} & {len(results[style]['no_reference'])} \\\\")
    parts.append("\\begin{tabular}{lrrrr}\n & Above & Below & Curated & No reference \\\\\n\\hline\n"
                 + "\n".join(rows) + "\n\\end{tabular}\n")
    for style in STYLES:
        res = results[style]
        parts.append(f"\\newpage\n\\subsection*{{{STYLE_TITLES[style]}}}\n")
        for cand in sorted(res["candidates"], key=lambda c: (c["cls"], c["cap"], c["glyph"])):
            parts.append(_format_candidate(style, cand, res["bases"][cand["glyph"]]))
        if res["no_reference"]:
            names = ", ".join(f"\\texttt{{\\detokenize{{{g}}}}}" for g in res["no_reference"])
            parts.append(f"Not tested, no glyph in regular: {names}.\n")
    return "\n".join(parts)


def write_mark_snap_sheet():
    """Build fonts/*-marksnap.otf and write tex/input/mark_snap.tex."""
    reg_offsets = _regular_offsets()
    results = {}
    for style in STYLES:
        font, cands, no_ref, capitals = snap_candidates(style, reg_offsets)
        anchored = _base_anchor_glyphs(font, f"{style}_patch")
        bases = {c["glyph"]: _bases(style, c, font, capitals, anchored) for c in cands}
        build_snap_font(style, font, cands)
        results[style] = {"candidates": cands, "no_reference": no_ref, "bases": bases}
        print(f"[{style}] {len(cands)} mark snap candidates, {len(no_ref)} without reference "
              f"-> {FONTS[f'{style}_marksnap']['path'].name}")
    path = TEX_INPUT_DIR / "mark_snap.tex"
    path.write_text(format_sheet(results), encoding="utf-8")
    print(f"-> {path}")
