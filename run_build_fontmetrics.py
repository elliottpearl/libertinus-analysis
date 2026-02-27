#!/usr/bin/env python3

# build_fontmetrics.py
#
# Extracts bounding boxes and legacy GPOS anchors from the
# original Libertinus fonts and writes them to JSON files
# in data/fontmetrics/.

from libertinus_analysis.fontmetrics_extractor import (
    extract_fontmetrics,
    write_fontmetrics_json,
)
from libertinus_analysis.font_context import FONTS

ORIGINAL_KEYS = [
    "regular",
    "italic",
    "semibold",
    "semibold_italic",
]

def build_all_fontmetrics():
    for font_key in ORIGINAL_KEYS:
        info = FONTS[font_key]
        lookup_index = info["lookup_index"]

        print(f"Extracting metrics for {font_key}...")

        data = extract_fontmetrics(font_key, lookup_index)
        write_fontmetrics_json(font_key, data)

        print(f"  → data/fontmetrics/{font_key}.json written.")

if __name__ == "__main__":
    build_all_fontmetrics()