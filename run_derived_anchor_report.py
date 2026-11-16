#!/usr/bin/env python3
"""
Write the derived-letter tables (stage 8 of the patch) and the stem-midline
check of the l-like and i-like letters into DERIVED-LETTERS.md, between its
GENERATED markers; the text around them is hand-written and kept. Run after
run_patch_font.py: it reads the original and patched fonts.

Until 2026-11-16 these were LaTeX tables in the report
(tex/input/derived_anchors.tex, tex/input/stem_check.tex).
"""

import re
from pathlib import Path

from libertinus_analysis.derived_anchors_report import (
    make_derived_anchors_markdown,
    make_stem_check_markdown,
)

MD_PATH = Path("DERIVED-LETTERS.md")

def replace_block(text, name, body):
    begin, end = f"<!-- BEGIN GENERATED: {name} -->", f"<!-- END GENERATED: {name} -->"
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise SystemExit(f"{MD_PATH}: markers for {name} not found")
    return pattern.sub(lambda _: f"{begin}\n\n{body}\n\n{end}", text)

def main():
    text = MD_PATH.read_text(encoding="utf-8")
    text = replace_block(text, "derived anchors", make_derived_anchors_markdown())
    text = replace_block(text, "stem check", make_stem_check_markdown())
    MD_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {MD_PATH}")

if __name__ == "__main__":
    main()
