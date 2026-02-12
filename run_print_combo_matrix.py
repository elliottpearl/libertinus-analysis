#!/usr/bin/env python3
"""
run_print_combo_matrix.py

Edit the configuration block below to choose:
- fonts
- base groups
- mark groups
- classifier
- builder: one of {"grid", "tabular", "paragraph"}
- output filename

This script writes a LaTeX fragment into tex/input/, which you can
`\input{}` from your main LaTeX document. 
Run xelatex manually.
"""

from libertinus_analysis.font_context import FONTS, FontContext
from libertinus_analysis.unicode_groups import base_groups, mark_groups
from libertinus_analysis.combo_matrix import ComboMatrix
from libertinus_analysis.classifiers import classify_attachment
from libertinus_analysis.config import TEX_INPUT_DIR


def print_combo_matrix(
    chosen_fonts,
    chosen_base_groups,
    chosen_mark_groups,
    classifier,
    builder,
    outfile,
):
    # Build font contexts
    font_contexts = {
        fk: FontContext.from_path(
            path=FONTS[fk]["path"],
            lookup_index=FONTS[fk]["lookup_index"],
            font_key=fk,
        )
        for fk in chosen_fonts
    }

    # Build ComboMatrix
    cm = ComboMatrix(
        base_groups={k: base_groups[k] for k in chosen_base_groups},
        mark_groups={k: mark_groups[k] for k in chosen_mark_groups},
        fonts={fk: FONTS[fk] for fk in chosen_fonts},
        classifier=classifier,
    )

    # Choose builder
    if builder == "grid":
        latex = cm.latex_grid()
    elif builder == "tabular":
        latex = cm.latex_tabular()
    elif builder == "paragraph":
        latex = cm.latex_paragraph()
    else:
        raise ValueError(f"Unknown builder: {builder}")

    # Write to tex/input/
    outpath = TEX_INPUT_DIR / outfile
    outpath.write_text(latex)
    print(f"Wrote LaTeX fragment to {outpath}")


if __name__ == "__main__":
    # ------------------------------------------------------------
    # HUMAN: choose report parameters here
    #
    # builder options:
    #   "grid"       → grid-style report
    #   "tabular"    → LaTeX tabular environment
    #   "paragraph"  → IPA-style paragraph report
    # ------------------------------------------------------------

    chosen_fonts = ["regular", "italic", "semibold"]

    chosen_base_groups = [
        # e.g. "latin_basic", "ipa_bases"
    ]

    chosen_mark_groups = [
        # e.g. "above", "below", "ipa_diacritics"
    ]

    classifier = classify_attachment
    builder = "grid"          # change to "tabular" or "paragraph"
    outfile = "my_report.tex" # name of the generated fragment

    print_combo_matrix(
        chosen_fonts=chosen_fonts,
        chosen_base_groups=chosen_base_groups,
        chosen_mark_groups=chosen_mark_groups,
        classifier=classifier,
        builder=builder,
        outfile=outfile,
    )