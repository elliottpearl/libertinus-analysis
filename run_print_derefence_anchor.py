#!/usr/bin/env python3
import sys
import fontforge

from libertinus_analysis.config import FONTS_DIR
from libertinus_analysis.dereference_anchor import analyze

def main():
    sfd_path = str(FONTS_DIR / "LibertinusSerif-Regular.sfd")


    try:
        font = fontforge.open(sfd_path)
    except Exception as e:
        print(f"Error opening SFD file '{sfd_path}': {e}")
        sys.exit(1)

    analyze(font)

if __name__ == "__main__":
    main()