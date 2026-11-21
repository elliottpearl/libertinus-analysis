# Dot letters: lowercase letters whose dot above (U+0307) or dot below
# (U+0323) is placed by the dot lookup, a second mark-to-base lookup that
# stage 9b of the patch (font_patching_dotanchors.py) appends after the main
# one. Where both lookups have an anchor for a base and mark, the dot lookup's
# position wins (HarfBuzz applies the lookups in order, and the later
# attachment replaces the earlier); every other base, and every other mark,
# keeps the main lookup's position.
#
# It restores the designer's dot convention over the reference-line model:
# in the precomposed letters the dot sits where it sits on an x-height letter,
# whatever the ascender or descender (ḃ ḋ ḣ at the height of ȧ ṅ, ỵ at the
# height of ạ ṇ, in all four styles). So the dot anchors are at the x-height
# reference (above) and the baseline reference (below), not at the ascender
# or descender, and X is over the letter's x-height body:
#     - from the designer's precomposed letter, where one has the dot there
#       (ḃ ḋ ḣ ỵ), so that the composed letter matches it;
#     - a derived letter (data/derived_letters.py) whose base letter is listed
#       inherits the base's dot anchor, moved by the fit of the base (fit_base);
#     - else the model's X for the x-height body (roman: midpoint of the ink
#       between the baseline and the x-height; italic: midline of the advance
#       lane at the anchor's height, minus K), pushed sideways only as far as
#       the dot needs to keep the designer's own smallest gap (MIN_GAP, the
#       closest dot of ḃ ḋ ḣ in the style).
# Precomposed letters of data/precomposed_letters.py whose base is listed here
# inherit its dot anchor (e.g. ḅ ḍ ḥ above, ý ÿ ỳ below).
#
# A letter goes in a list only after the test sheet (run_dot_lookup_sheet.py)
# shows the dot clear of it in every style, or with a style exception below.
#
# Lists of codepoints; exclusions as {codepoint: (styles or None, reason)},
# None meaning every style.

DOT_ABOVE = [
    0x0062,  # b  (ḃ)
    0x0064,  # d  (ḋ)
    0x0068,  # h  (ḣ)
    0x006B,  # k  over the arm
    0x00FE,  # þ  thorn
    0x0257,  # ɗ  d with hook (derived from d)
    0x0260,  # ɠ  g with hook
    0x02A0,  # ʠ  q with hook
    0x026E,  # ɮ  lezh, over the ezh
    0x2C68,  # ⱨ  h with descender (derived from h)
    0x2C6A,  # ⱪ  k with descender
]

DOT_BELOW = [
    0x0070,  # p
    0x0071,  # q
    0x0079,  # y  (ỵ)
    0x00FE,  # þ  thorn
    0x0272,  # ɲ  n with left hook
    0x0273,  # ɳ  n with retroflex hook
    0x0271,  # ɱ  m with hook
    0x0265,  # ɥ  turned h
    0x02AE,  # ʮ  turned h with fishhook
    0x02AF,  # ʯ  turned h with fishhook and tail
    0x024F,  # ɏ  y with stroke (derived from y)
    0x01B4,  # ƴ  y with hook
    0xA765,  # ꝥ  thorn with stroke (derived from þ)
]
# A letter belongs in a list only if its dot is clear in all four styles
# (gap at least MIN_GAP - 6, or the designer's own precomposed position) and
# sits over the letter's body. The test sheet (run_dot_lookup_sheet.py)
# computes which candidates fail in some style or have no clear position;
# the exclusions below are the judgement calls among the rest, so that the
# sheet's "open" group holds only letters nobody has decided yet.

EXCLUDED_ABOVE = {
    0x028E: (None, "turned y: a dot at the x-height looks odd; keep the ascender reference (2026-11-20)"),
    0x0140: (None, "ŀ: the dot lands on the middle dot, not over a body"),
    0x0234: (None, "ȴ: the dot lands over the curl, beside the stem"),
    0x026C: (None, "ɬ: the dot lands beside the stem, over the belt"),
    0x0278: (None, "ɸ: the dot lands beside the stem, over the bowl's side"),
    0x0192: (None, "ƒ: the dot lands beside the stem"),
    0x027A: (None, "ɺ: the dot lands beside the stem, over the arm"),
}

EXCLUDED_BELOW = {
    0x014B: (None, "ŋ: the hook curls under the letter, so the dot goes under the left stem; Gentium, Charis, Noto, Junicode put marks under the descender (2026-11-20)"),
    0x0066: (None, "f: descends only in the italics; the dot lands beside the stem, far from the curl (decide with the f question, TODO.md)"),
    0x00DF: (None, "ß: descends only in the italics; the dot lands beside the descender"),
    0x0192: (None, "ƒ: the dot lands beside the stem"),
    0x0285: (None, "ʅ: the dot lands beside the hook"),
    0x017F: (None, "ſ: descends only in the italics"),
    0x025F: (None, "ɟ: the dot lands beside the stem, under the bar"),
    0x0284: (None, "ʄ: the dot lands beside the stem"),
    0x027C: (None, "ɼ: the dot lands beside the long leg"),
    0x0267: (None, "ɧ: the dot lands beside the hook"),
}

# The vertical line above (U+030D) and below (U+0329) go into the dot lookup
# too, with the dot's anchor, where listed here (tested on the sheet).
LINE_ABOVE = True    # 2026-11-20: every listed letter's line gap within 1 of its gap on o (semibold d 42 vs 52)
LINE_BELOW = False   # 2026-11-20: collides on the italic y family (y ɏ 17, ƴ 9); semibold p q þ ƴ ꝥ 26-30 vs 39 on o
