#!/usr/bin/env python3

from libertinus_analysis.anchor_copy_analysis import (
    analyze_union_per_style,
    analyze_union_all_styles,
)
from libertinus_analysis.fontmetrics_loader import load_all_fontmetrics

def main():
    all_metrics = load_all_fontmetrics()

    analyze_union_per_style(all_metrics, min_cluster_size=2)
    analyze_union_all_styles(all_metrics, min_cluster_size=3)

if __name__ == "__main__":
    main()
