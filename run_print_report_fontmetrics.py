#!/usr/bin/env python3
"""
Wrapper script to generate a LaTeX fontmetrics report.
"""

from pathlib import Path

from libertinus_analysis.fontmetrics_report import (
    make_fontmetrics_table,
    wrap_in_table_environment,
)
from libertinus_analysis.config import TEX_INPUT_DIR
from data.ipa.ipa_unicode import unicode_groups

# Simple helper for continuous Unicode ranges
def bases_from_unicode_range(start_cp: int, end_cp: int):
    return [chr(cp) for cp in range(start_cp, end_cp + 1)]

# Main wrapper logic
def main():
    # ------------------------------------------------------------------
    # Choose ONE base set by uncommenting it.
    #
    # Continuous ranges:
    # bases = bases_from_unicode_range(0x0041, 0x005A)   # A–Z
    bases = bases_from_unicode_range(0x0061, 0x007A)   # a–z
    # bases = bases_from_unicode_range(0x0250, 0x02AF)   # IPA block
    # bases = bases_from_unicode_range(0x0100, 0x017F)   # Latin Ext‑A
    # bases = bases_from_unicode_range(0x0370, 0x03FF)   # Greek
    # bases = bases_from_unicode_range(0x0400, 0x04FF)   # Cyrillic
    #
    # IPA groups (direct access):
    # bases = [chr(cp) for cp in unicode_groups["VOWELS"]["items"]]
    # bases = [chr(cp) for cp in unicode_groups["CONSONANTS"]["items"]]
    # bases = [chr(cp) for cp in unicode_groups["BASE_IPA"]["items"]]
    #
    # Example: IPA vowels minus ASCII a–z
    # az = {ord(c) for c in bases_from_unicode_range(0x0061, 0x007A)}
    # vowels = unicode_groups["VOWELS"]["items"]
    # bases = [chr(cp) for cp in vowels if cp not in az]
    #
    # Optional: split into two halves
    mid = len(bases) // 2
    bases_1 = bases[:mid]
    bases_2 = bases[mid:]
    # ------------------------------------------------------------------

    # tag for latex label and filename
    # tag = "az"
    tag = "az2"
    # Human readable caption
    mycaption = "a--z"

    # table_body = make_fontmetrics_table(bases_1)
    table_body = make_fontmetrics_table(bases)

    # Wrap in a full LaTeX table environment
    latex_table = wrap_in_table_environment(
        table_body,
        caption=f"Font metrics for {mycaption}",
        label=f"table:fontmetrics_{tag}",
    )

    # Write to tex/input/
    out_path = TEX_INPUT_DIR / f"fontmetrics_{tag}.tex"
    out_path.write_text(latex_table, encoding="utf-8")

    print(f"Wrote LaTeX fontmetrics report to: {out_path}")


if __name__ == "__main__":
    main()
