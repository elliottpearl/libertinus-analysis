#!/usr/bin/env python3
"""
Wrapper script to generate all LaTeX fontmetrics reports.
"""

import math
from pathlib import Path

from libertinus_analysis.fontmetrics_report import (
    make_fontmetrics_table,
    make_fontmetrics_table_for_marks,
    wrap_in_table_environment,
)
from libertinus_analysis.config import TEX_INPUT_DIR
from data.ipa.ipa_unicode import unicode_groups

def main():

    # Columns per table; cells hold "X, Y" pairs.
    MAX_COLS = {"base": 18, "mark": 18}

    def chunks(seq, max_size):
        """Split seq into the fewest chunks of at most max_size, of even size."""
        parts = math.ceil(len(seq) / max_size)
        size = math.ceil(len(seq) / parts)
        for i in range(0, len(seq), size):
            yield seq[i:i+size]

    # --- Precompute sets ---
    ascii_upper = set(range(0x0041, 0x005A + 1))
    ascii_lower = set(range(0x0061, 0x007A + 1))
    ascii_all = ascii_upper | ascii_lower

    base_latin = set(unicode_groups["BASE_LATIN"]["items"])
    base_ipa = set(unicode_groups["BASE_IPA"]["items"])

    # BASE_LATIN minus ASCII
    latin_remainder = base_latin - ascii_all

    # Union with IPA
    latin_plus_ipa = sorted(latin_remainder | base_ipa)

    # --- Define table sources ---
    table_sources = [
        ("AZ", "A--Z",
         [chr(cp) for cp in sorted(ascii_upper)],
         "base"),

        ("az", "a--z",
         [chr(cp) for cp in sorted(ascii_lower)],
         "base"),

        ("latinIPA", "Latin and IPA",
         [chr(cp) for cp in latin_plus_ipa],
         "base"),

        ("above", "above marks",
         [chr(cp) for cp in unicode_groups["MARK_ABOVE"]["items"]],
         "mark", "0"),

        ("below", "below marks",
         [chr(cp) for cp in unicode_groups["MARK_BELOW"]["items"]],
         "mark", "2"),
    ]

    # --- Loop over all table sources ---
    for entry in table_sources:
        tag = entry[0]
        caption = entry[1]
        glyphs = entry[2]
        kind = entry[3]
        anchor_id = entry[4] if kind == "mark" else None

        subsets = list(chunks(glyphs, MAX_COLS[kind]))
        tables = []
        for idx, subset in enumerate(subsets, start=1):
            # Label suffix (underscores OK) and caption suffix (LaTeX-safe)
            if len(subsets) > 1:
                label_suffix = f"_{idx}"
                caption_suffix = f" {idx}/{len(subsets)}"
            else:
                label_suffix = ""
                caption_suffix = ""

            if kind == "base":
                table_body = make_fontmetrics_table(subset)
            else:
                table_body = make_fontmetrics_table_for_marks(subset, anchor_id)

            tables.append(wrap_in_table_environment(
                table_body,
                caption=f"Font metrics for {caption}{caption_suffix}",
                label=f"table:fontmetrics_{tag}{label_suffix}",
            ))

        # One file per group, holding all its tables
        out_path = TEX_INPUT_DIR / f"fontmetrics_{tag}.tex"
        out_path.write_text("\n".join(tables), encoding="utf-8")
        print(f"Wrote {out_path} ({len(tables)} tables)")

if __name__ == "__main__":
    main()
