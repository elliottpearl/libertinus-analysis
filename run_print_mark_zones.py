#!/usr/bin/env python3

# run_print_mark_zones.py
#
# Writes one TikZ figure per style to tex/input/mark_zones_<style>.tex,
# from the patched fonts. run_patch_font.py does this too.

from libertinus_analysis.mark_zones import write_mark_zone_figures

if __name__ == "__main__":
    write_mark_zone_figures()
