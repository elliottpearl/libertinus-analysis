#!/usr/bin/env python3
"""
run_precomposed_existing_report.py

Precomposed letters in stage 9's lists that keep a designer or curated anchor,
compared with what stage 9 would inherit -> tex/input/precomposed_existing.tex.
Run from the repo root after run_patch_font.py.
"""

from libertinus_analysis.precomposed_existing_report import write_report

if __name__ == "__main__":
    path, total = write_report()
    print(f"Wrote {total} rows to {path}")
