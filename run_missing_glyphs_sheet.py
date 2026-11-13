#!/usr/bin/env python3

from libertinus_analysis.missing_glyphs import build_drafts, write_sheet

# Reads the patched fonts: run after run_patch_font.py.
# Writes fonts/*-draft.otf and tex/missing_glyphs_test_sheet.tex;
# PDF: cd tex && xelatex missing_glyphs_test_sheet.tex
notes, checks, status = build_drafts()
print(write_sheet(notes, checks, status))
