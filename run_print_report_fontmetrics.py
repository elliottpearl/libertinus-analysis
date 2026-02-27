#!/usr/bin/env python3
"""
Wrapper script to generate a LaTeX fontmetrics report.

This script lives OUTSIDE the src/ directory.
It imports the package normally and writes the output into tex/input/.
"""

from pathlib import Path

from libertinus_analysis.report_fontmetrics import (
    make_fontmetrics_table,
    wrap_in_table_environment,
)
from libertinus_analysis.config import TEX_INPUT_DIR


# ----------------------------------------------------------------------
# Base selection helpers
# ----------------------------------------------------------------------

def bases_from_unicode_range(start_cp: int, end_cp: int):
    """Return a list of characters for a continuous Unicode range."""
    return [chr(cp) for cp in range(start_cp, end_cp + 1)]


def bases_from_ipa_group(group_key: str):
    """
    Load bases from a specific IPA subgroup defined in
    data/ipa/ipa_unicode.py::unicode_groups.

    The human operator is expected to know the symbolic keys, such as:

        "VOWELS"
        "SYLLABIC_SONORANTS"
        "PALATALIZABLE"
        "RETROFLEX_CONSONANTS"
        "BASE_IPA"
        "BASE_LATIN"
        "BASE_GREEK"
        "BASE_CYRILLIC"
        "BASE_SMALL_CAPITAL"
        ...

    Each entry in unicode_groups looks like:

        unicode_groups[group_key] = {
            "label": "Printable name",
            "items": <python list of codepoints>,
        }

    This function returns a list of characters corresponding to those codepoints.
    """

    from data.ipa.ipa_unicode import unicode_groups

    if group_key not in unicode_groups:
        available = ", ".join(unicode_groups.keys())
        raise KeyError(
            f"IPA group '{group_key}' not found. "
            f"Available groups: {available}"
        )

    cps = unicode_groups[group_key]["items"]
    return [chr(cp) for cp in cps]


# ----------------------------------------------------------------------
# Main wrapper logic
# ----------------------------------------------------------------------

def main():
    # ------------------------------------------------------------------
    # Choose ONE base set by uncommenting it.
    #
    # These presets use the continuous-range helper. They are simple,
    # predictable, and easy to modify. The IPA subgroup option is also
    # available for fine-grained selections.
    #
    # A–Z (uppercase Latin)
    # bases = bases_from_unicode_range(0x0041, 0x005A)
    #
    # a–z (lowercase Latin)
    # bases = bases_from_unicode_range(0x0061, 0x007A)
    #
    # IPA block (U+0250–U+02AF)
    # bases = bases_from_unicode_range(0x0250, 0x02AF)
    #
    # Latin Extended‑A (U+0100–U+017F)
    # bases = bases_from_unicode_range(0x0100, 0x017F)
    #
    # Greek (U+0370–U+03FF)
    # bases = bases_from_unicode_range(0x0370, 0x03FF)
    #
    # Cyrillic (U+0400–U+04FF)
    # bases = bases_from_unicode_range(0x0400, 0x04FF)
    #
    # IPA subgroup by symbolic key (from ipa_unicode.py::unicode_groups)
    # Examples:
    #   "VOWELS"
    #   "SYLLABIC_SONORANTS"
    #   "PALATALIZABLE"
    #   "RETROFLEX_CONSONANTS"
    #   "BASE_IPA"
    #   "BASE_LATIN"
    #   ...
    # bases = bases_from_ipa_group("VOWELS")
    #
    # Default choice:
    bases = bases_from_unicode_range(0x0041, 0x005A)  # A–Z
    # bases = bases_from_unicode_range(0x0061, 0x007A)    # a-z
    # bases = bases_from_ipa_group("VOWELS")
    # ------------------------------------------------------------------

    # Convert bases to codepoint strings ("0x0041" style)
    codepoints = [f"0x{ord(b):04X}" for b in bases]

    # Generate the LaTeX table body
    table_body = make_fontmetrics_table(codepoints, bases)

    # Wrap in a full LaTeX table environment
    latex_table = wrap_in_table_environment(
        table_body,
        caption="Font metrics for A--Z",
        label="table:fontmetrics_AZ"
    )

    # Write to tex/input/
    out_path = TEX_INPUT_DIR / "fontmetrics_AZ.tex"
    out_path.write_text(latex_table, encoding="utf-8")

    print(f"Wrote LaTeX fontmetrics report to: {out_path}")


if __name__ == "__main__":
    main()