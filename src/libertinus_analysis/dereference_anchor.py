import fontforge

from .config import FONTS_DIR

from data.ipa.ipa_unicode import (
    PRECOMPOSED_CAPITAL_VOWELS,
    PRECOMPOSED_SMALL_VOWELS,
    PRECOMPOSED_CAPITAL_CONSONANTS,
    PRECOMPOSED_SMALL_CONSONANTS,
)

PRECOMPOSED_ALL = set(
    PRECOMPOSED_CAPITAL_VOWELS +
    PRECOMPOSED_SMALL_VOWELS +
    PRECOMPOSED_CAPITAL_CONSONANTS +
    PRECOMPOSED_SMALL_CONSONANTS
)

# ------------------------------------------------------------
# Helper: find anchor by name
# ------------------------------------------------------------

def anchors_by_name(glyph, name):
    return [a for a in glyph.anchorPoints if a[0] == name]

# ------------------------------------------------------------
# Main analysis
# ------------------------------------------------------------

def analyze(font):
    for g in font.glyphs():
        if g.unicode is None or g.unicode not in PRECOMPOSED_ALL:
            continue

        refs = g.references
        if len(refs) != 2:
            print(f"U+{g.unicode:04X} {g.glyphname}: not built from exactly 2 references (has {len(refs)})")
            continue

        print(f"U+{g.unicode:04X} {g.glyphname}:")

        # Precomposed glyph's own base 'above' anchor (if any)
        base_above = None
        for a in g.anchorPoints:
            if a[0] == "above" and a[1] == "base":
                base_above = (a[2], a[3])
                break

        # Process each referenced component
        for i, (refname, transform, *_) in enumerate(refs):

            refglyph = font[refname]
            a, b, c, d, tx, ty = transform

            print(f"  component {i}: {refname} (U+{refglyph.unicode:04X}) tx={tx} ty={ty}")

            # 1) If referenced glyph has 'above' mark/basemark → implied base anchor
            for a in refglyph.anchorPoints:
                name, kind, ax, ay = a
                if name == "above" and kind in ("mark", "basemark"):
                    implied_x = tx + ax
                    implied_y = ty + ay
                    print(f"    implied base 'above' from {refname}.above({kind}): "
                          f"({implied_x:.1f}, {implied_y:.1f})")

            # 2) If referenced glyph has 'above' base anchor and precomposed has base_above → implied mark anchor
            if base_above is not None:
                for a in refglyph.anchorPoints:
                    name, kind, ax, ay = a
                    if name == "above" and kind == "base":
                        mx = base_above[0] - tx
                        my = base_above[1] - ty
                        print(f"    implied mark 'above' for {refname}: ({mx:.1f}, {my:.1f})")

            # 3) If referenced glyph has 'aboveMark' basemark anchor → implied mark-to-mark anchor
            if base_above is not None:
                for a in refglyph.anchorPoints:
                    name, kind, ax, ay = a
                    if name == "aboveMark":
                        mmx = base_above[0] - tx
                        mmy = base_above[1] - ty
                        print(f"    implied mark-to-mark 'aboveMark' for {refname}: "
                              f"({mmx:.1f}, {mmy:.1f})")

        print()
