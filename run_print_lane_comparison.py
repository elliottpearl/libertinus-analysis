#!/usr/bin/env python3
"""
Lane comparison for the italic base-anchor candidate X: advance lane (the
model) vs ink lane. Writes tex/input/lane_comparison_*.tex for
tex/lane-comparison.tex (a separate PDF; the report does not \\input them).
Run from the repo root, then: cd tex && xelatex lane-comparison.tex
"""

import math

from libertinus_analysis.config import TEX_INPUT_DIR
from libertinus_analysis.fontmetrics_report import wrap_in_table_environment
from libertinus_analysis.lane_comparison_report import make_lane_table, make_summary_table
from data.ipa.ipa_unicode import unicode_groups
import data.derived_letters as derived_letters

MAX_COLS = 18


def chunks(seq, max_size):
    parts = math.ceil(len(seq) / max_size)
    size = math.ceil(len(seq) / parts)
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def main():
    upper = list(range(0x41, 0x5B))
    lower = list(range(0x61, 0x7B))
    base_latin = set(unicode_groups["BASE_LATIN"]["items"])
    base_ipa = set(unicode_groups["BASE_IPA"]["items"])
    rest = sorted((base_latin - set(upper) - set(lower)) | base_ipa)

    all_cps = sorted(set(upper) | set(lower) | set(rest))
    summary = make_summary_table(all_cps, set(derived_letters.derived))
    (TEX_INPUT_DIR / "lane_comparison_summary.tex").write_text(summary, encoding="utf-8")

    for tag, caption, cps in [("AZ", "A--Z", upper), ("az", "a--z", lower),
                              ("latinIPA", "Latin and IPA", rest)]:
        subsets = list(chunks([chr(c) for c in cps], MAX_COLS))
        tables = []
        for i, subset in enumerate(subsets, start=1):
            suffix = f" {i}/{len(subsets)}" if len(subsets) > 1 else ""
            tables.append(wrap_in_table_environment(
                make_lane_table(subset),
                caption=f"Lane comparison for {caption}{suffix}",
                label=f"table:lanes_{tag}_{i}",
            ))
        out = TEX_INPUT_DIR / f"lane_comparison_{tag}.tex"
        out.write_text("\n".join(tables), encoding="utf-8")
        print(f"Wrote {out} ({len(tables)} tables)")


if __name__ == "__main__":
    main()
