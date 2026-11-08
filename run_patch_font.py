#!/usr/bin/env python3

from libertinus_analysis.font_patching import patch_font
from libertinus_analysis.mark_zones import write_mark_zone_figures

patch_font("regular")
patch_font("italic")
patch_font("semibold")
patch_font("semibold_italic")

# The mark zone figures read the patched fonts.
write_mark_zone_figures()
