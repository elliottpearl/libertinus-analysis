#!/usr/bin/env python3
"""
run_anchor_copy_report.py

Generate a LaTeX fragment showing copied-anchor clusters
for all styles (regular, italic, semibold, semibold italic).

The output is written to tex/input/copied_anchors.tex
and can be \\input{} from your main LaTeX document.
"""

from libertinus_analysis.anchor_copy_analysis import (
    analyze_union_per_style,
)
from libertinus_analysis.fontmetrics_loader import load_all_fontmetrics
from libertinus_analysis.config import TEX_INPUT_DIR

# NEW: our TeX formatter
from libertinus_analysis.anchor_copy_texformatter import (
    format_all_styles_tex,
)


def main():
    # Load all font metrics (your existing function)
    all_metrics = load_all_fontmetrics()

    # Run your existing per-style cluster analysis
    # (min_cluster_size=2 is what you used before)
    results = analyze_union_per_style(all_metrics, min_cluster_size=2)

    # Convert results → LaTeX fragment
    latex = format_all_styles_tex(results)

    # Write to tex/input/
    outfile = "copied_anchors.tex"
    outpath = TEX_INPUT_DIR / outfile
    outpath.write_text(latex, encoding="utf8")

    print(f"Wrote copied-anchor LaTeX fragment to {outpath}")


if __name__ == "__main__":
    main()
