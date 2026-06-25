#!/usr/bin/env python3
import sys
import io
import fontforge
from contextlib import redirect_stdout
from pathlib import Path

from fontTools.ttLib import TTFont

from libertinus_analysis.config import FONTS_DIR
from libertinus_analysis.implied_cap_marks import (
    load_cmap,
    compute_cap_mark_implied_anchors,
    summarize_cap_mark_results,
)

OUT_DIR = Path("data/fontanchors_implied")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    font_keys = [
        "regular",
        "italic",
        "semibold",
        "semibold_italic",
    ]

    sfd_names = {
        "regular": "LibertinusSerif-Regular.sfd",
        "italic": "LibertinusSerif-Italic.sfd",
        "semibold": "LibertinusSerif-Semibold.sfd",
        "semibold_italic": "LibertinusSerif-SemiboldItalic.sfd",
    }

    otf_names = {
        "regular": "LibertinusSerif-Regular.otf",
        "italic": "LibertinusSerif-Italic.otf",
        "semibold": "LibertinusSerif-Semibold.otf",
        "semibold_italic": "LibertinusSerif-SemiboldItalic.otf",
    }

    for key in font_keys:
        sfd_path = FONTS_DIR / sfd_names[key]
        otf_path = FONTS_DIR / otf_names[key]
        out_path = OUT_DIR / f"cap_marks_{key}.txt"

        # Load cmap from OTF
        if not otf_path.exists():
            print(f"[{key}] ERROR: OTF not found: {otf_path}")
            continue

        try:
            cmap = load_cmap(str(otf_path))
        except Exception as e:
            print(f"[{key}] ERROR loading cmap from '{otf_path}': {e}")
            continue

        # Load SFD with FontForge (suppress stdout noise)
        if not sfd_path.exists():
            print(f"[{key}] ERROR: SFD not found: {sfd_path}")
            continue

        ff_buf = io.StringIO()
        with redirect_stdout(ff_buf):
            try:
                font = fontforge.open(str(sfd_path))
            except Exception as e:
                print(f"[{key}] ERROR opening SFD '{sfd_path}': {e}")
                continue

        # Compute implied anchors
        results, warnings = compute_cap_mark_implied_anchors(font, cmap)
        report = summarize_cap_mark_results(results, warnings)

        out_path.write_text(report, encoding="utf-8")
        print(f"[{key}] wrote {out_path} ({len(report)} chars)")


if __name__ == "__main__":
    main()
