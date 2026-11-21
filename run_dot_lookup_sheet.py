#!/usr/bin/env python3

from libertinus_analysis.dot_lookup_sheet import write_dot_lookup_sheet

# Reads the patched fonts: run after run_patch_font.py.
# Writes fonts/*-patch-nodot.otf, fonts/*-patch-dotcand.otf and tex/dot_lookup_test_sheet.tex;
# PDF: cd tex && xelatex dot_lookup_test_sheet.tex
write_dot_lookup_sheet()
