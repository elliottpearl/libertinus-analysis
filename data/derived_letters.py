# Derived letters: letters drawn as a base letter plus a bar, stroke, hook,
# tail, curl or belt, and the anchor classes they may inherit from it.
#
# Stage 8 of the patch pipeline (font_patching_derivedanchors.py) gives a
# derived letter the base letter's final anchor, moved by the horizontal shift
# at which the base's outline best matches the derived letter's outline (the
# designer often drew the derived letter shifted, e.g. Ɗ is D moved ~80 right).
# It inherits only in styles where enough of the base's outline is found in the
# derived letter (MIN_MATCH in that module), and never over a curated anchor.
#
# A class is listed only where the added part stays clear of that mark:
#     bar, stroke or belt through the letter     above and below (0, 2)
#     hook at the top, away from the centre      above and below (0, 2)
#     hook, tail or curl at the bottom           above only (0)
#     hook at the top in the mark's way          below only (2)
#
# In italic and semibold italic, d and h have their above-anchor at the
# x-height, over the bowl or arch beside the ascender; there a bar or hook
# near the top of the ascender is in the mark's way, so đ ħ ɗ ɦ inherit only
# below in those styles.
#
# derived codepoint -> (base codepoint, anchor classes), where the classes
# are a tuple for every style, or a dict {style: tuple} where they differ.

# Above and below in the roman styles, below only in the italic styles
_ROMAN_ONLY_ABOVE = {
    "regular": (0, 2), "semibold": (0, 2),
    "italic": (2,), "semibold_italic": (2,),
}

derived = {
    # --- bar or stroke ---
    0x00D0: (0x0044, (0, 2)),  # Ð eth < D
    0x0110: (0x0044, (0, 2)),  # Đ D with stroke < D
    0x0189: (0x0044, (0, 2)),  # Ɖ African D < D
    0x0111: (0x0064, _ROMAN_ONLY_ABOVE),  # đ d with stroke < d
    0x0126: (0x0048, (0, 2)),  # Ħ H with stroke < H
    0x0127: (0x0068, _ROMAN_ONLY_ABOVE),  # ħ h with stroke < h
    0x0141: (0x004C, (0, 2)),  # Ł L with stroke < L
    0x0142: (0x006C, (0, 2)),  # ł l with stroke < l
    0x00D8: (0x004F, (0, 2)),  # Ø O with stroke < O; the slash ends off-centre
    0x00F8: (0x006F, (0, 2)),  # ø o with stroke < o
    0x019F: (0x004F, (0, 2)),  # Ɵ O with middle tilde (barred O) < O
    0x0275: (0x006F, (0, 2)),  # ɵ barred o < o
    0x0197: (0x0049, (0, 2)),  # Ɨ I with stroke < I
    0x0268: (0x0069, (2,)),    # ɨ i with stroke < i (above: see derived_by_name)
    0x0289: (0x0075, (0, 2)),  # ʉ u bar < u
    0x026B: (0x006C, (0, 2)),  # ɫ l with middle tilde < l
    0x026C: (0x006C, (0, 2)),  # ɬ l with belt < l
    0x025F: (0x0237, (0, 2)),  # ɟ dotless j with stroke < ȷ
    # --- hook at the top, away from the centre ---
    0x0181: (0x0042, (0, 2)),  # Ɓ B with hook < B
    0x018A: (0x0044, (0, 2)),  # Ɗ D with hook < D
    0x0187: (0x0043, (0, 2)),  # Ƈ C with hook < C
    0x0193: (0x0047, (0, 2)),  # Ɠ G with hook < G
    0x0198: (0x004B, (0, 2)),  # Ƙ K with hook < K
    0x0253: (0x0062, (0, 2)),  # ɓ b with hook < b
    0x0257: (0x0064, _ROMAN_ONLY_ABOVE),  # ɗ d with hook < d
    0x0266: (0x0068, _ROMAN_ONLY_ABOVE),  # ɦ h with hook < h
    0x029B: (0x0262, (0, 2)),  # ʛ small capital G with hook < ɢ
    # --- hook at the top in the mark's way ---
    0x025D: (0x025C, (2,)),    # ɝ reversed open e with hook < ɜ
    0x025A: (0x0259, (2,)),    # ɚ schwa with hook < ə
    0x0284: (0x0237, (2,)),    # ʄ dotless j with stroke and hook < ȷ
    # --- hook, tail or curl at the bottom ---
    0x0191: (0x0046, (0,)),    # Ƒ F with hook < F
    0x019D: (0x004E, (0,)),    # Ɲ N with left hook < N
    0x0255: (0x0063, (0,)),    # ɕ c with curl < c
    0x0256: (0x0064, (0,)),    # ɖ d with tail < d
    0x026D: (0x006C, (0,)),    # ɭ l with retroflex hook < l
    0x0271: (0x006D, (0,)),    # ɱ m with hook < m
    0x0272: (0x006E, (0,)),    # ɲ n with left hook < n
    0x0273: (0x006E, (0,)),    # ɳ n with retroflex hook < n
    0x027B: (0x0279, (0,)),    # ɻ turned r with hook < ɹ
    0x027D: (0x0072, (0,)),    # ɽ r with tail < r
    0x0282: (0x0073, (0,)),    # ʂ s with hook < s
    0x0286: (0x0283, (0,)),    # ʆ esh with curl < ʃ
    0x0288: (0x0074, (0,)),    # ʈ t with retroflex hook < t
    0x0290: (0x007A, (0,)),    # ʐ z with retroflex hook < z
    0x0291: (0x007A, (0,)),    # ʑ z with curl < z
    0x0293: (0x0292, (0,)),    # ʓ ezh with curl < ʒ
}

# Not derived, though the Unicode name says so: the outline is a different
# letterform, or matches the base too little in every style.
#     Ƃ U+0182 B with topbar, Ƌ U+018B D with topbar, ʋ U+028B v with hook,
#     ƒ U+0192 f with hook (curated), ɠ U+0260 g with hook

# Unencoded forms, by glyph name: the dotless forms that ccmp substitutes
# before an above mark.
#
# derived glyph name -> (base glyph name, anchor classes)

derived_by_name = {
    "uni0268.dotless": ("dotlessi", (0,)),  # ɨ before an above mark < ı
}
