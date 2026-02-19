#!/usr/bin/env python3
"""
run.py - Driver script for Libertinus analysis
"""

from pathlib import Path

# Project imports

from libertinus_analysis import constants
from libertinus_analysis import geometry
from libertinus_analysis import shaping


"""
# Driver tasks
# Expose exactly the task you want to run.

# Inspect bounding boxes for a font
# 
# bboxes = get_bboxes_with_names(fonts["regular"]["path"])
# print_bboxes_list(bboxes)

# Compute new anchor positions for superscript consonants
# 
# compute_baseanchor3()   # anchor class 3 (left angle above)
# compute_baseanchor0()   # anchor class 0 (acute/grave/circumflex)

# Patch a font's GPOS MarkBasePos table
# 
# patch_gpos_font(
#    fonts["regular"]["path"],
#    fonts["regular_patch"]["path"],
#)   

# Generate TeX grids for multiple groups
# Prints to stdout; redirect to file `tex/inputs/*.tex` as needed.
# 
# shaping.print_combos(
#   base_lists = select_bases("latin", "ipa"),
#   mark_lists = select_marks("above", "below"),
# )

# shaping.print_combos(
#  base_lists = select_bases("base_anchor_required"),
#  mark_lists = select_marks("mark_anchor_required"),
#)

# Generate IPA diacritic base glyph list
# Prints to stdout; redirect to file `tex/inputs/*.tex` as needed.
#
# shaping.print_ipa_diacritics()
"""