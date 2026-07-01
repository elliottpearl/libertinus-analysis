# anchor_copy_analysis.py

from __future__ import annotations

from collections import defaultdict

from libertinus_analysis.fontmetrics_loader import load_all_fontmetrics, get_anchor
from data.ipa.ipa_unicode import unicode_groups


# ----------------------------------------------------------------------
# EXACT same base groups as your fontmetrics report, minus marks
# ----------------------------------------------------------------------

BASE_GROUPS = {
    "AZ": list(range(0x0041, 0x005A + 1)),
    "az": list(range(0x0061, 0x007A + 1)),
    "latinIPA": (
        list(unicode_groups["BASE_LATIN"]["items"]) +
        list(unicode_groups["BASE_IPA"]["items"])
    ),
}


# ----------------------------------------------------------------------
# Collect anchors for a list of codepoints
# ----------------------------------------------------------------------

def collect_anchor_pairs(style_metrics: dict, cps: list[int]):
    above = defaultdict(list)
    below = defaultdict(list)

    for cp in cps:
        a0 = get_anchor(style_metrics, cp, "0")
        a2 = get_anchor(style_metrics, cp, "2")

        if a0:
            above[(int(a0[0]), int(a0[1]))].append(cp)
        if a2:
            below[(int(a2[0]), int(a2[1]))].append(cp)

    return above, below


# ----------------------------------------------------------------------
# Cluster detection
# ----------------------------------------------------------------------

def find_clusters(anchor_dict: dict, min_size: int):
    return [
        (pair, cps)
        for pair, cps in anchor_dict.items()
        if len(cps) >= min_size
    ]


# ----------------------------------------------------------------------
# Union all base groups per style
# ----------------------------------------------------------------------

def union_all_groups_per_style():
    cps = []
    for group_cps in BASE_GROUPS.values():
        cps.extend(group_cps)
    return sorted(set(cps))


# ----------------------------------------------------------------------
# Per-style union analysis
# ----------------------------------------------------------------------

def analyze_union_per_style(all_metrics, min_cluster_size: int = 3):
    print("\n=== UNION PER STYLE ===")

    base_union = union_all_groups_per_style()
    results = {}

    for style_key, style_metrics in all_metrics.items():
        above_pairs, below_pairs = collect_anchor_pairs(style_metrics, base_union)

        above_clusters = find_clusters(above_pairs, min_cluster_size)
        below_clusters = find_clusters(below_pairs, min_cluster_size)

        print(f"\n  -- Style: {style_key} --")
        print(f"    glyphs scanned: {len(base_union)}")
        print(f"    above pairs: {len(above_pairs)}")
        print(f"    below pairs: {len(below_pairs)}")

        if above_clusters:
            print("    Above-anchor clusters:")
            for (ax, ay), cps in above_clusters:
                hexes = " ".join(f"{cp:04X}" for cp in cps)
                chars = " ".join(chr(cp) for cp in cps)
                print(f"      ({ax}, {ay}) → {hexes}")
                print(f"        chars: {chars}")

        if below_clusters:
            print("    Below-anchor clusters:")
            for (bx, by), cps in below_clusters:
                hexes = " ".join(f"{cp:04X}" for cp in cps)
                chars = " ".join(chr(cp) for cp in cps)
                print(f"      ({bx}, {by}) → {hexes}")
                print(f"        chars: {chars}")

        results[style_key] = {
            "above": above_clusters,
            "below": below_clusters,
        }

    return results


# ----------------------------------------------------------------------
# Super-union across all styles
# ----------------------------------------------------------------------

def analyze_union_all_styles(all_metrics, min_cluster_size: int = 3):
    print("\n=== SUPER-UNION ACROSS ALL STYLES ===")

    cps = union_all_groups_per_style()

    above = defaultdict(list)
    below = defaultdict(list)

    for style_key, style_metrics in all_metrics.items():
        for cp in cps:
            a0 = get_anchor(style_metrics, cp, "0")
            a2 = get_anchor(style_metrics, cp, "2")

            if a0:
                above[(int(a0[0]), int(a0[1]))].append((style_key, cp))
            if a2:
                below[(int(a2[0]), int(a2[1]))].append((style_key, cp))

    above_clusters = [
        (pair, entries)
        for pair, entries in above.items()
        if len(entries) >= min_cluster_size
    ]
    below_clusters = [
        (pair, entries)
        for pair, entries in below.items()
        if len(entries) >= min_cluster_size
    ]

    print(f"    glyphs scanned: {len(cps)}")
    print(f"    above pairs: {len(above)}")
    print(f"    below pairs: {len(below)}")

    if above_clusters:
        print("\n    Above-anchor clusters across styles:")
        for (ax, ay), entries in above_clusters:
            listing = " ".join(f"{style}:{cp:04X}" for style, cp in entries)
            chars = " ".join(chr(cp) for (_, cp) in entries)
            print(f"      ({ax}, {ay}) → {listing}")
            print(f"        chars: {chars}")

    if below_clusters:
        print("\n    Below-anchor clusters across styles:")
        for (bx, by), entries in below_clusters:
            listing = " ".join(f"{style}:{cp:04X}" for style, cp in entries)
            chars = " ".join(chr(cp) for (_, cp) in entries)
            print(f"      ({bx}, {by}) → {listing}")
            print(f"        chars: {chars}")

    return {
        "above": above_clusters,
        "below": below_clusters,
    }
