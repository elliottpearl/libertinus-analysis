#!/usr/bin/env python3
"""
run_print_combo_matrix.py

Edit the configuration block below to choose:
- fonts
- base groups
- mark groups
- classifier
- builder
- output filename

This script writes a LaTeX fragment into tex/input/, 
which can be \\input{} from the main LaTeX document. 
Run xelatex manually.
"""

from libertinus_analysis.font_context import FontContext
from libertinus_analysis import ipa_base_groups, ipa_mark_groups, FONTS
from libertinus_analysis.combo_matrix import ComboMatrix
from libertinus_analysis.classifiers import (
    classify_combo,
    classify_combo_sanity
)
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
        base_groups={k: ipa_base_groups[k] for k in chosen_base_groups},
        mark_groups={k: ipa_mark_groups[k] for k in chosen_mark_groups},
        fonts={fk: FONTS[fk] for fk in chosen_fonts},
        classifier=classifier,
    )

    cm.load_fonts()
    cm.classify()

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
    # HUMAN: choose report parameters here

    # keys of FONTS of font_context.py
    # "regular", "italic", "semibold", "semibold_italic", "regular_patch"
    chosen_fonts = [
        "regular",
    ]

    # keys of ipa_base_groups of ipa_unicode.py
    # e.g. "latin", "ipa", "base_anchor_required"
    chosen_base_groups = [
        "latin",
    ]

    # keys of ipa_mark_groups of ipa_unicode.py
    # e.g. "above", "below", "mark_anchor_required"
    chosen_mark_groups = [
        "above",        
    ]

    # classify_combo or classify_combo_sanity
    classifier = classify_combo

    # "grid" or "tabular" or "paragraph"
    builder = "grid"          

    # LaTeX filename in TEX_INPUT = "tex/input/"
    # e.g. "latin_above.tex" 
    outfile = "latin_above.tex" 

    print_combo_matrix(
        chosen_fonts=chosen_fonts,
        chosen_base_groups=chosen_base_groups,
        chosen_mark_groups=chosen_mark_groups,
        classifier=classifier,
        builder=builder,
        outfile=outfile,
    )
