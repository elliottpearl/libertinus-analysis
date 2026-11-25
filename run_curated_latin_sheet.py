#!/usr/bin/env python3

from libertinus_analysis.curated_latin_sheet import write_curated_latin_sheet

# Reads the patched fonts and data/anchor_provenance: run after run_patch_font.py.
# Writes fonts/*-patch-nocur.otf, fonts/*-patch-cand.otf and tex/curated_latin_test_sheet.tex;
# PDF: cd tex && xelatex curated_latin_test_sheet.tex
write_curated_latin_sheet()
