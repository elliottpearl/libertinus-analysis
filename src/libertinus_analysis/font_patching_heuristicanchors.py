# font_patching_heuristicanchors.py
"""
Heuristic-anchor stage of the Libertinus patching pipeline (stage 6).

Gives every base in BASE_LATIN and BASE_IPA that lacks an above (class 0) or
below (class 2) anchor the anchor candidate of the anchor model
(get_anchor_candidate in fontmetrics_helpers.py; ANCHOR-HEURISTICS.md):
    Y: the ideal bounding box edge plus the clearance (get_aya / get_bya);
    X: roman → bbox midpoint; italic → W/2 + Y tan(theta) - K.

Only missing anchors are added; an existing anchor is never moved. The
candidates are computed from the original font's fontmetrics JSON, which
holds the same base outlines as the patched font.

Skipped:
    - glyphs with a canonical Unicode decomposition: stage 8 lets them
      inherit the anchors of their base;
    - glyphs missing from the font or from the fontmetrics JSON.

Human-curated anchors (stage 7) overrule the anchors added here.
"""

import unicodedata

from libertinus_analysis import unicode_groups
from .fontmetrics_helpers import get_anchor_candidate
from .fontmetrics_loader import load_fontmetrics
from .font_patching_precomposed_anchors import (
    ensure_base_record_for_glyph,
    find_mark_to_base_subtables,
    get_anchor_from_baserec,
    get_base_record_for_glyph,
    set_anchor_in_baserec,
)

BASE_GROUPS = ["BASE_LATIN", "BASE_IPA"]
ANCHOR_CLASSES = {0: "above", 2: "below"}

def _is_canonically_decomposed(cp: int) -> bool:
    raw = unicodedata.decomposition(chr(cp))
    return bool(raw) and not raw.startswith("<")

def patch_anchors_heuristic(ttfont, font_key, lookup_index):
    """
    Add the candidate above/below anchor to each base lacking one.

    font_key: "regular", "italic", "semibold" or "semibold_italic"; the
    fontmetrics JSON and the style tables are keyed by it.

    Returns: list of report lines.
    """
    report = []

    subtables = find_mark_to_base_subtables(ttfont, lookup_index)
    if not subtables:
        return [f"No MarkToBase (LookupType 4) subtables found in lookup {lookup_index}; SKIPPED"]
    sub = subtables[0]

    metrics = load_fontmetrics(font_key)
    cmap = ttfont.getBestCmap()

    codepoints = sorted({cp for g in BASE_GROUPS for cp in unicode_groups[g]["items"]})

    added = 0
    for cp in codepoints:
        if cp not in cmap or _is_canonically_decomposed(cp):
            continue
        glyph_name = cmap[cp]

        for anchor_class, anchor_name in ANCHOR_CLASSES.items():
            baserec, _ = get_base_record_for_glyph(sub, glyph_name)
            if baserec is not None and get_anchor_from_baserec(baserec, anchor_class) is not None:
                continue

            cand = get_anchor_candidate(font_key, metrics, cp, str(anchor_class))
            if cand is None:
                report.append(f"{glyph_name}: no fontmetrics for U+{cp:04X}; {anchor_name} anchor SKIPPED")
                continue

            x, y, ideal = cand
            x, y = round(x), round(y)
            baserec, _ = ensure_base_record_for_glyph(sub, glyph_name)
            set_anchor_in_baserec(baserec, anchor_class, x, y)
            report.append(f"{glyph_name}: added heuristic {anchor_name} anchor ({x}, {y}), ideal {ideal}")
            added += 1

    report.append(f"heuristic anchors added: {added}")
    return report
