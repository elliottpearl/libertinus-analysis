#!/usr/bin/env python3
"""
Write the test sheet for derived-letter anchors (stage 8 of the patch) to
tex/input/derived_anchors.tex. Run after run_patch_font.py: it reads the
original and patched fonts.
"""

from libertinus_analysis.config import TEX_INPUT_DIR
from libertinus_analysis.derived_anchors_report import make_derived_anchors_tables

def main():
    out_path = TEX_INPUT_DIR / "derived_anchors.tex"
    out_path.write_text(make_derived_anchors_tables(), encoding="utf-8")
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
