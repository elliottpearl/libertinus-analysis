# Derived letters: letters drawn as a base letter plus a bar, stroke, hook,
# tail, curl or belt, and the anchor classes they may inherit from it.
#
# Stage 8 of the patch pipeline (font_patching_derivedanchors.py) gives a
# derived letter the base letter's final anchor, moved by the fit of the base
# letter inside the derived letter (a shift, and a scale of up to 15%, on the
# inherited side: fit_base, as stage 9; the designer often drew the derived
# letter shifted, e.g. Ɗ is D moved ~80 right, and the italic capitals with a
# hook or bar ~4% wider). It inherits only where the fit reaches MIN_FIT, per
# class and style, and never over a curated anchor. See stem_match and
# stem_axis for the exceptions.
#
# A class is listed only where the added part stays clear of that mark:
#     bar, stroke or belt through the letter     above and below (0, 2)
#     hook at the top, away from the centre      above and below (0, 2)
#     hook, tail or curl at the bottom           above and below (0, 2), see bottom_tail
#     hook at the top in the mark's way          below only (2)
#
# In italic and semibold italic, d and h had their above-anchor at the
# x-height, over the bowl beside the ascender, where a bar or hook near the
# top of the ascender is in the mark's way. Both are now at the ascender
# reference (deleted in stage 1, candidate in stage 6), and đ ɗ inherit above
# in every style (2026-11-06); ħ ɦ still inherit only below there.
#
# derived codepoint -> (base codepoint, anchor classes), where the classes
# are a tuple for every style, or a dict {style: tuple} where they differ.

# Above and below in the roman styles, below only in the italic styles
_ROMAN_ONLY_ABOVE = {
    "regular": (0, 2), "semibold": (0, 2),
    "italic": (2,), "semibold_italic": (2,),
}

derived = {
    # ɮ lezh < l: above over the l (regular's curated "centre of l", 2026-11-07); below is the ezh's, curated
    0x026E: (0x006C, (0,)),
    # --- bar or stroke ---
    0x00D0: (0x0044, (0, 2)),  # Ð eth < D
    0x0110: (0x0044, (0, 2)),  # Đ D with stroke < D
    0x0189: (0x0044, (0, 2)),  # Ɖ African D < D
    0x0111: (0x0064, (0, 2)),  # đ d with stroke < d
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
    0x02A1: (0x0294, (0, 2)),  # ʡ glottal stop with stroke < ʔ (epiglottal plosive; 2026-11-11)
    0x02A2: (0x0295, (0, 2)),  # ʢ reversed glottal stop with stroke < ʕ (epiglottal fricative)
    0x2C62: (0x004C, (0, 2)),  # Ɫ L with middle tilde < L (stem_axis)
    0x019A: (0x006C, (0, 2)),  # ƚ l with bar < l (stem_axis)
    0x2C60: (0x004C, (0, 2)),  # Ⱡ L with double bar < L
    0x2C61: (0x006C, (0, 2)),  # ⱡ l with double bar < l (stem_axis)
    0x023D: (0x004C, (0, 2)),  # Ƚ L with bar < L
    0x0166: (0x0054, (0, 2)),  # Ŧ T with stroke < T
    0x0167: (0x0074, (0, 2)),  # ŧ t with stroke < t
    0x023E: (0x0054, (0, 2)),  # Ⱦ T with diagonal stroke < T
    0x2C66: (0x0074, (0, 2)),  # ⱦ t with diagonal stroke < t
    0x01E4: (0x0047, (0, 2)),  # Ǥ G with stroke < G
    0x01E5: (0x0067, (0, 2)),  # ǥ g with stroke < g
    0x023A: (0x0041, (0, 2)),  # Ⱥ A with stroke < A
    0x2C65: (0x0061, (0, 2)),  # ⱥ a with stroke < a
    0x023B: (0x0043, (0, 2)),  # Ȼ C with stroke < C
    0x023C: (0x0063, (0, 2)),  # ȼ c with stroke < c
    0xA793: (0x0063, (0, 2)),  # ꞓ c with bar < c (regular only)
    0x0243: (0x0042, (0, 2)),  # Ƀ B with stroke < B
    0x0180: (0x0062, (0, 2)),  # ƀ b with stroke < b
    0x0246: (0x0045, (0, 2)),  # Ɇ E with stroke < E (regular only)
    0x0247: (0x0065, (0, 2)),  # ɇ e with stroke < e
    0x0248: (0x004A, (0, 2)),  # Ɉ J with stroke < J
    0x0249: (0x006A, (2,)),    # ɉ j with stroke < j (above: see derived_by_name)
    0x024C: (0x0052, (0, 2)),  # Ɍ R with stroke < R (regular only)
    0x024D: (0x0072, (0, 2)),  # ɍ r with stroke < r
    0x024E: (0x0059, (0, 2)),  # Ɏ Y with stroke < Y (regular only)
    0x024F: (0x0079, (0, 2)),  # ɏ y with stroke < y (regular only)
    0x2C63: (0x0050, (0, 2)),  # Ᵽ P with stroke < P
    0x01B5: (0x005A, (0, 2)),  # Ƶ Z with stroke < Z
    0x01B6: (0x007A, (0, 2)),  # ƶ z with stroke < z
    0x1E9C: (0x017F, (0, 2)),  # ẜ long s with diagonal stroke < ſ
    0x1E9D: (0x017F, (0, 2)),  # ẝ long s with high stroke < ſ
    0xA765: (0x00FE, (0, 2)),  # ꝥ thorn with stroke < þ (regular only)
    # --- middle dot (compatibility decomposition only, so not stage 9's) ---
    0x013F: (0x004C, (0, 2)),  # Ŀ L with middle dot < L
    0x0140: (0x006C, (0, 2)),  # ŀ l with middle dot < l
    # --- other ---
    0x0269: (0x0131, (0, 2)),  # ɩ iota < ı
    # --- hook at the top, away from the centre ---
    0x0181: (0x0042, (0, 2)),  # Ɓ B with hook < B
    0x018A: (0x0044, (0, 2)),  # Ɗ D with hook < D
    0x0187: (0x0043, (0, 2)),  # Ƈ C with hook < C
    0x0193: (0x0047, (0, 2)),  # Ɠ G with hook < G
    0x0198: (0x004B, (0, 2)),  # Ƙ K with hook < K
    # ɓ U+0253: see derived_y
    0x0257: (0x0064, (0, 2)),  # ɗ d with hook < d; matched on stems (stem_match)
    0x0266: (0x0068, _ROMAN_ONLY_ABOVE),  # ɦ h with hook < h
    0x029B: (0x0262, (0, 2)),  # ʛ small capital G with hook < ɢ
    # Group 4, 2026-11-11: letters with a hook, topbar or ring that stays clear of both marks
    0x01A4: (0x0050, (0, 2)),  # Ƥ P with hook < P
    0x0183: (0x0062, (0, 2)),  # ƃ b with topbar < b (unlike Ƃ, which is not derived)
    0x018C: (0x0064, (0, 2)),  # ƌ d with topbar < d (unlike Ƌ)
    0x01B3: (0x0059, (0, 2)),  # Ƴ Y with hook < Y (stem_axis)
    0x01B4: (0x0079, (0, 2)),  # ƴ y with hook < y
    0x0199: (0x006B, (0, 2)),  # ƙ k with hook < k
    0x0188: (0x0063, (0, 2)),  # ƈ c with hook < c
    0x1E9A: (0x0061, (0, 2)),  # ẚ a with right half ring < a: the ring stays out of the mark's zone
    0xAB52: (0x0075, (0, 2)),  # ꭒ u with left hook < u (regular only)
    0x01AC: (0x0054, (0, 2)),  # Ƭ T with hook < T (stem_axis: the hook at the bar's end spoils the fit above)
    # Group 4: a hook rising from the stem to the ascender, in the above mark's way: below inherits;
    # above in derived_y, at the ascender reference
    0x01A5: (0x0070, (2,)),    # ƥ p with hook < p
    0x02A0: (0x0071, (2,)),    # ʠ q with hook < q
    0x01AD: (0x0074, (2,)),    # ƭ t with hook < t (stem_axis below)
    # --- hook at the top in the mark's way ---
    0x025D: (0x025C, (2,)),    # ɝ reversed open e with hook < ɜ
    0x025A: (0x0259, (2,)),    # ɚ schwa with hook < ə
    0x0284: (0x0283, (0, 2)),  # ʄ dotless j with stroke and hook < ʃ: Libertinus draws it as ʃ with a bar (match 95%;
                               # ȷ 56-76%) (2026-11-07)
    # --- hook, tail or curl at the bottom ---
    0x0191: (0x0046, (0, 2)),    # Ƒ F with hook < F
    0x019D: (0x004E, (0, 2)),    # Ɲ N with left hook < N
    0x0255: (0x0063, (0,)),      # ɕ c with curl < c
    0x0256: (0x0064, (0, 2)),    # ɖ d with tail < d
    0x026D: (0x006C, (0, 2)),    # ɭ l with retroflex hook < l
    0x0271: (0x006D, (0, 2)),    # ɱ m with hook < m
    0x0272: (0x006E, (0, 2)),    # ɲ n with left hook < n
    0x0273: (0x006E, (0, 2)),    # ɳ n with retroflex hook < n
    0x027B: (0x0279, (0, 2)),    # ɻ turned r with hook < ɹ
    0x0285: (0x027F, (0,)),      # ʅ squat reversed esh < ɿ: redrawn in stage 2 as ɿ with ɳ's retroflex hook
                                 # (2026-11-09). Above only: below is stage 6's candidate, on the redrawn outline
                                 # (the tail rule here would read the original outline's fontmetrics)
    0x027D: (0x0072, (0, 2)),    # ɽ r with tail < r
    0x0282: (0x0073, (0, 2)),    # ʂ s with hook < s
    0x0286: (0x0283, (0, 2)),    # ʆ esh with curl < ʃ
    0x0288: (0x0074, (0, 2)),    # ʈ t with retroflex hook < t
    0x0290: (0x007A, (0, 2)),    # ʐ z with retroflex hook < z
    0x0291: (0x007A, (0, 2)),    # ʑ z with curl < z
    0x0293: (0x0292, (0, 2)),    # ʓ ezh with curl < ʒ
    # Group 4, 2026-11-11
    0x01AB: (0x0074, (0, 2)),    # ƫ t with palatal hook < t
    0x01AE: (0x0054, (0, 2)),    # Ʈ T with retroflex hook < T
    0x0221: (0x0064, (0, 2)),    # ȡ d with curl < d
    0x0234: (0x006C, (0, 2)),    # ȴ l with curl < l
    0x0235: (0x006E, (0, 2)),    # ȵ n with curl < n
    0x0236: (0x0074, (0, 2)),    # ȶ t with curl < t
    0x2C64: (0x0052, (0, 2)),    # Ɽ R with tail < R (stems match only in regular; elsewhere stage 6's candidate)
    0x2C67: (0x0048, (0, 2)),    # Ⱨ H with descender < H: the descender is clear of the mark
    0x2C68: (0x0068, (0, 2)),    # ⱨ h with descender < h
    0x2C69: (0x004B, (0, 2)),    # Ⱪ K with descender < K (regular only matches)
    0x2C6A: (0x006B, (0, 2)),    # ⱪ k with descender < k (regular only matches)
    0x2C6E: (0x004D, (0, 2)),    # Ɱ M with hook < M (regular only)
    0x1EFF: (0x0079, (0, 2)),    # ỿ y with loop < y (regular only)
    # Not derived: Ⱬ ⱬ (Z and z have no stems, so a stem match is chance); stage 6 gives them candidates
}

# Bottom-tail letters: the hook, tail or curl at the bottom. Stage 8 matches
# them on the stems and bowl sides above the tail (stem_shift), not on the
# whole outline, since the tail replaces the base letter's foot. Below, where
# the tail has ink within reach of the widest below mark of the mark's axis,
# Y is the anchor-model candidate (descender reference) and X the base
# letter's plus the shift; where the tail is clear of the mark (Ɲ), Y is the
# base letter's. Where the stems match too little, the above anchor is not
# inherited, and a below anchor over a tail gets the candidate, X and Y.
# Decided 2026-11-06 for all such letters, whether the tail curls toward the
# centre or away from it: a dot below clears an outward tail at the baseline,
# but the wide below marks do not.

bottom_tail = {
    0x0191, 0x019D, 0x0255, 0x0256, 0x026D, 0x0271, 0x0272, 0x0273,
    0x027B, 0x027D, 0x0282, 0x0285, 0x0286, 0x0288, 0x0290, 0x0291, 0x0293,
    # Group 4, 2026-11-11
    0x01AB, 0x01AE, 0x0221, 0x0234, 0x0235, 0x0236, 0x2C64, 0x2C67, 0x2C68,
    0x2C69, 0x2C6A, 0x2C6E, 0x1EFF,
}

# Letters matched on their stems (stem_shift) rather than their whole
# outline: the bottom-tail letters, and ɗ, whose hook replaces the top of the
# ascender (whole-outline match 50-53% in semibold and semibold italic, stem
# match 82-92%). The tail rule for the below anchor does nothing where there
# is no tail.

stem_match = bottom_tail | {0x0257}

# Letters placed on their own stem: an l, ı or ȷ whose bar, belt or tilde
# crosses the stem. X is the base letter's plus the shift between the two stems'
# midlines (measured where the outline is a single stem-wide interval), Y the
# base letter's; whatever the fit, since the stem decides (2026-11-11: the
# fit drops semibold italic ɫ ɬ ɩ below, at 62-69%, though their anchors lie
# on the stem).

stem_axis = {0x026B, 0x026C, 0x0269, 0x019A, 0x2C61, 0x2C62,
             0x025F,  # ɟ (see below)
             0x01AC, 0x01AD,  # Ƭ ƭ: T's and t's stem (Group 4, 2026-11-11)
             0x01B3,  # Ƴ: Y moved 58-94 right for the hook; its fit fails above in the semibold styles
             0x023E}  # Ⱦ: the stroke rises above the bar, so the fit fails above in italic (74%); the Y move clears it
# ɟ: fits ȷ 55-69% (the bar), so its above anchor was a candidate, 36 left of the stem in semibold

# Anchors with a Y of their own, where the base letter's Y does not apply: X
# still comes from the base letter's final anchor, plus the outline shift, and
# follows the slant to this Y. Unlike the classes above, this applies whatever
# the outline match, since only the X is borrowed.
#
# derived codepoint -> (base codepoint, {class: {style: Y}})

derived_y = {
    # ɓ b with hook < b: above and below at b's Y, X b's plus the outline shift, whatever the match (2026-11-07):
    # the whole-outline match is 42-90% because of the hook, but the counters of b and ɓ agree within 6 in every style
    0x0253: (0x0062, {0: {"regular": 885, "italic": 890, "semibold": 885, "semibold_italic": 890},
                      2: {"regular": -110, "italic": -110, "semibold": -121, "semibold_italic": -110}}),
    # ʝ j with crossed tail < j: above, X as j (on the stem), Y j's own (dot top + clearance): ʝ has no dotless
    # form, so every above mark clears its dot, as the few that skip j's dotless swap (2026-11-07); outline match 52-64%
    0x029D: (0x006A, {0: {
        "regular": 834, "italic": 810, "semibold": 837, "semibold_italic": 823,
    }}),
    # ɠ g with hook < ɡ (script g, U+0261, not g): above, X as ɡ, Y at the ascender reference over the hook
    # (regular's curated (239, 885), 2026-11-07); outline match 82-97%
    0x0260: (0x0261, {0: {
        "regular": 885, "italic": 890, "semibold": 885, "semibold_italic": 890,
    }}),
    # ɕ c with curl < c: below, Y is the anchor model's, under the curl
    0x0255: (0x0063, {2: {
        "regular": -214, "italic": -208, "semibold": -209, "semibold_italic": -209,
    }}),
    # Group 4, 2026-11-11: the hook rises from the stem to the ascender, so above marks sit at the
    # ascender reference, as on ɠ; X from the base letter plus the outline shift
    0x01A5: (0x0070, {0: {"regular": 885, "italic": 890, "semibold": 885, "semibold_italic": 890}}),  # ƥ < p
    0x02A0: (0x0071, {0: {"regular": 885, "italic": 890, "semibold": 885, "semibold_italic": 890}}),  # ʠ < q
    0x01AD: (0x0074, {0: {"regular": 885, "italic": 890, "semibold": 885, "semibold_italic": 890}}),  # ƭ < t
    # ɼ r with long leg < r: above only; below is curated, under the stem
    0x027C: (0x0072, {0: {
        "regular": 645, "italic": 645, "semibold": 645, "semibold_italic": 645,
    }}),
}

# Not derived, though the Unicode name says so: the outline is a different
# letterform, or matches the base too little in every style.
#     Ƃ U+0182 B with topbar, Ƌ U+018B D with topbar, ʋ U+028B v with hook,
#     ƒ U+0192 f with hook (curated); ɠ U+0260 g with hook matches g too little (derived_y from ɡ instead)

# Unencoded forms, by glyph name: the dotless forms that ccmp substitutes
# before an above mark.
#
# derived glyph name -> (base glyph name, anchor classes)

derived_by_name = {
    "uni0268.dotless": ("dotlessi", (0, 2)),  # ɨ before an above mark < ı; below too, for a below mark
                                               # after the above mark (the designer's was 22 left of the stem)
    "uni0249.dotless": ("uni0237", (0, 2)),   # ɉ before an above mark < ȷ (2026-11-11)
    # ɿ with descender, U+E27F (PUA), added in stage 2 as ɿ's top and q's descender serif (2026-11-09).
    # Above as ɿ; below is curated, under the stem at the descender reference
    "uni027F.desc": ("uni027F", (0,)),
}
