# lane_comparison_report.py
"""
Fontmetrics tables comparing two italic lanes for the base-anchor candidate X:
the advance lane (the model, midline W/2 + Y tan theta) and the ink lane (the
narrowest strip at the italic angle containing the outline, midline
C + Y tan theta, C = axis_x). Y is the same for both. Only the two italic
styles are shown: in roman both lanes give the bbox midpoint.

Each delta is the original font's (designer's) anchor minus the candidate.
The summary also compares the curated anchors of data/fontanchors_human.
Written by run_print_lane_comparison.py for tex/lane-comparison.tex.
"""
from __future__ import annotations

import importlib
import statistics as st
import unicodedata as ud

from .fontmetrics_loader import load_all_fontmetrics, get_anchor
from .fontmetrics_helpers import get_anchor_candidate
from .fontmetrics_report import (
    SAMPLE_STRUT, STYLE_LABELS, build_header_rows, sample_letter_glyph, texify,
)

ITALIC_STYLES = ["italic", "semibold_italic"]
LANES = ["advance", "ink"]
LANE_LABELS = {"advance": "adv", "ink": "ink"}
CLASSES = [("0", "a"), ("2", "b")]


def _deltas(style_key, style_metrics, cp, anchor_id, anchor):
    """{lane: (candidate, delta)} for one anchor; delta None without anchor."""
    out = {}
    for lane in LANES:
        cand = get_anchor_candidate(style_key, style_metrics, cp, anchor_id, lane=lane)
        if cand is None:
            return None
        delta = (anchor[0] - cand[0], anchor[1] - cand[1]) if anchor else None
        out[lane] = (cand, delta)
    return out


def make_lane_table(bases: list[str]) -> str:
    """One column per base; per italic style: samples, then for a and b the
    anchor, and candidate and delta per lane. The smaller |X delta| is bold."""
    cps = [ord(c) for c in bases]
    all_metrics = load_all_fontmetrics()
    rows = build_header_rows(cps)
    for style_key in ITALIC_STYLES:
        sm = all_metrics[style_key]
        rows.append(["\\hline " + STYLE_LABELS[style_key] + SAMPLE_STRUT]
                    + [sample_letter_glyph(cp, style_key) for cp in cps])
        rows.append(["patch" + SAMPLE_STRUT]
                    + [sample_letter_glyph(cp, f"{style_key}_patch") for cp in cps])
        for anchor_id, prefix in CLASSES:
            have = []
            cand_rows = {lane: [] for lane in LANES}
            delta_rows = {lane: [] for lane in LANES}
            for cp in cps:
                anchor = get_anchor(sm, cp, anchor_id)
                have.append(f"{round(anchor[0])}, {round(anchor[1])}" if anchor else "")
                d = _deltas(style_key, sm, cp, anchor_id, anchor)
                if d is None:
                    for lane in LANES:
                        cand_rows[lane].append("")
                        delta_rows[lane].append("")
                    continue
                dx = {lane: d[lane][1][0] for lane in LANES} if anchor else None
                for lane in LANES:
                    cand, delta = d[lane]
                    cand_rows[lane].append(f"{round(cand[0])}, {round(cand[1])}")
                    if delta is None:
                        delta_rows[lane].append("")
                        continue
                    cell = f"{round(delta[0])}, {round(delta[1])}"
                    other = dx["ink" if lane == "advance" else "advance"]
                    if abs(round(delta[0])) < abs(round(other)):
                        cell = f"\\textbf{{{cell}}}"
                    delta_rows[lane].append(cell)
            rows.append([prefix] + have)
            for lane in LANES:
                rows.append([f"{prefix}? {LANE_LABELS[lane]}"] + cand_rows[lane])
                rows.append([f"{prefix}$\\delta$ {LANE_LABELS[lane]}"] + delta_rows[lane])
    return texify(rows)


# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------

def _curated_bases(style_key):
    """{cp: {class: (x, y)}} of the active curated base anchors."""
    mod = importlib.import_module(f"data.fontanchors_human.{style_key}")
    return mod.anchors.get("bases", {})


def _stats(dxs):
    if not dxs:
        return None
    a = [abs(v) for v in dxs]
    return (len(dxs), st.median(a), st.mean(a), sum(v <= 10 for v in a), st.median(dxs))


def _collect(style_key, sm, cps, source, exclude=frozenset()):
    """{class: {lane: [dx, ...]}} and {class: [wins advance, wins ink, ties]}."""
    curated = _curated_bases(style_key) if source == "curated" else None
    dx = {c: {lane: [] for lane in LANES} for c, _ in CLASSES}
    wins = {c: [0, 0, 0] for c, _ in CLASSES}
    for cp in cps:
        if cp in exclude:
            continue
        for anchor_id, _ in CLASSES:
            if source == "curated":
                anchor = curated.get(cp, {}).get(int(anchor_id))
            else:
                anchor = get_anchor(sm, cp, anchor_id)
            if not anchor:
                continue
            d = _deltas(style_key, sm, cp, anchor_id, anchor)
            if d is None:
                continue
            ad, ik = d["advance"][1][0], d["ink"][1][0]
            dx[anchor_id]["advance"].append(ad)
            dx[anchor_id]["ink"].append(ik)
            r = abs(round(ad)) - abs(round(ik))
            wins[anchor_id][0 if r < 0 else 1 if r > 0 else 2] += 1
    return dx, wins


def make_summary_table(cps: list[int], derived: set[int]) -> str:
    """Rows per style, source and class: n, median |dX|, mean |dX|, within 10,
    median signed dX, per lane, and how many anchors each lane is closer to."""
    all_metrics = load_all_fontmetrics()
    precomposed = {cp for cp in cps
                   if ud.decomposition(chr(cp)) and not ud.decomposition(chr(cp)).startswith("<")}
    sources = [
        ("designer", "designer, all", frozenset()),
        ("designer", "designer, no derived or precomposed", frozenset(derived | precomposed)),
        ("curated", "curated", frozenset()),
    ]
    head = ("style & anchors & class & $n$ & "
            "\\multicolumn{4}{c}{advance lane} & \\multicolumn{4}{c}{ink lane} & "
            "\\multicolumn{3}{c}{closer} \\\\\n"
            " & & & & med & mean & ${\\le}10$ & sgn & med & mean & ${\\le}10$ & sgn & "
            "adv & ink & tie \\\\\n\\hline\n")
    lines = []
    for style_key in ITALIC_STYLES:
        sm = all_metrics[style_key]
        for source, label, excl in sources:
            dx, wins = _collect(style_key, sm, cps, source, excl)
            for anchor_id, prefix in CLASSES:
                sa, si = _stats(dx[anchor_id]["advance"]), _stats(dx[anchor_id]["ink"])
                if not sa:
                    continue
                cells = [STYLE_LABELS[style_key], label, prefix, str(sa[0])]
                for s in (sa, si):
                    cells += [f"{s[1]:.1f}", f"{s[2]:.1f}", str(s[3]), f"{s[4]:.0f}"]
                cells += [str(w) for w in wins[anchor_id]]
                lines.append(" & ".join(cells) + " \\\\")
        lines.append("\\hline")
    return ("\\begin{tabular}{lllrrrrrrrrrrrr}\n" + head + "\n".join(lines)
            + "\n\\end{tabular}\n")
