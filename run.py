#!/usr/bin/env python3
"""
run.py — Driver script for Libertinus analysis.

Imports the reusable libraries (geometry.py and shaping.py) 
and exposes a set of clearly marked "uncomment to run" tasks.
"""

from pathlib import Path
import sys

# Add project root to sys.path so imports work regardless of cwd
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

# Import constants and tool modules

from data.constants import (
    fonts,
    select_marks,
    select_bases,
)

from scripts.geometry import (
    get_bboxes_with_names,
    print_bboxes_list,
    compute_baseanchor0,
    compute_baseanchor3,
    patch_gpos_font,
)

from scripts.shaping import (
    print_combos,
    print_ipa_diacritics
)

# Driver tasks
# Uncomment exactly the task you want to run.

# Inspect bounding boxes for a font
# 
# bboxes = get_bboxes_with_names(fonts["regular"]["path"])
# print_bboxes_list(bboxes)

# Compute new anchor positions for superscript consonants
# 
# compute_baseanchor3()   # anchor class 3 (left angle above)
# compute_baseanchor0()   # anchor class 0 (acute/grave/circumflex)

# Patch a font’s GPOS MarkBasePos table
# 
# patch_gpos_font(
#    fonts["regular"]["path"],
#    fonts["regular_patch"]["path"],
#)   

# Generate TeX grids for multiple groups
# Prints to stdout; redirect to file `tex/inputs/*.tex` as needed.
# 
# print_combos(
#   base_lists = select_bases("latin", "ipa"),
#   mark_lists = select_marks("above", "below"),
# )

# print_combos(
#  base_lists = select_bases("base_anchor_required"),
#  mark_lists = select_marks("mark_anchor_required"),
#)

# Generate IPA diacritic base glyph list
# Prints to stdout; redirect to file `tex/inputs/*.tex` as needed.
#
# print_ipa_diacritics()