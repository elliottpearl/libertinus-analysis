#!/usr/bin/env python3

# run_print_mark_zones.py
#
# Writes one TikZ figure per style to tex/input/mark_zones_<style>.tex,
# from the patched fonts: run after run_patch_font.py.

from libertinus_analysis.config import TEX_INPUT_DIR
from libertinus_analysis.mark_zones import STYLE_KEYS, mark_zone_figure

if __name__ == "__main__":
    for style_key in STYLE_KEYS:
        figure, count = mark_zone_figure(style_key)
        path = TEX_INPUT_DIR / f"mark_zones_{style_key}.tex"
        path.write_text(figure, encoding="utf-8")
        print(f"{path.name}: {count} marks")
