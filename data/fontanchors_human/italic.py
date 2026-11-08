# Anchor data
# 0 above. 2 below

anchors = {
    "bases": {
        0x0044: { # D: above (2026-11-07). The designer's (396, 850) is 70-80 left of the marks of Ď (467) and Ḋ (478)
                  # at y 850; the candidate (514, 850) rejected, 40 right of them. The upper-ink centroid (y > 330) is 490,
                  # and regular's designer D sits 22 left of its centroid, giving 468. X: mean of Ď, Ḋ, 468.
            0: (471, 850),
        },
        0x0045: { # E: below (2026-11-07). The designer's (269, -110) pulled left toward the evidence, at y -110:
                  # Ḙ 230, Ẹ 222, Ḛ 198 (mark centres, which the mark anchors reproduce), candidate 240 (mean 222).
                  # X: midway between the designer and that mean.
            2: (246, -110),
        },
        0x0048: { # H: above on the midline between the stems (2026-11-07). The designer's (481, 850), the same as V's,
                  # puts marks 23 left of it; the candidate (517) 13 right. Ĥ and Ḣ put theirs at 502-504
            0: (504, 850),
        },
        0x004C: { # L: above on the stem's axis (2026-11-07), not 75 right as the designer's (389, 850), where the designer centred the acute of Ĺ (10 right)
            0: (314, 850),
        },
        0x04F: { # O
            0: (493, 850), # above: median accent centre of the precomposed Ò Ó Ô Õ Ö Ō Ŏ … (479-502); the designer's 515 was 22 right,
                           # exposed by the top of the bowl; Ø inherits it (2026-11-07)
            2: (310, -110) # normalize by
        },
        0x0055: { # U: above at the median accent centre of the precomposed Ù Ú Û Ü Ũ Ū Ŭ … (497-511), like O (2026-11-07);
                  # on its stems' midline it was 494
            0: (508, 850),
        },
        0x0056: { # V: above on the bisector of the arms (2026-11-07). The designer's (481, 850), the same as H's, puts marks
                  # 23 right of it; U's marks land 8 left of its midline, Y's 11 right of its arms' bisector
            0: (458, 850),
        },
        0x0059: { # Y: above at the median accent centre of the precomposed Ý Ŷ Ÿ Ẏ Ỳ (432-453), like O (2026-11-07);
                  # on its arms' bisector it was 424
            0: (441, 850),
        },
        # 0x0059: { # Y
             # 2: (270, -110) # Y normalize  # removed 2026-10-29: designer's anchor is (270, -109)
        # },
        0x0061: { # a
            # 2: (251, -110),  # was (174, -108). x-mid of (78,175.5) to (423.5,75.5) on right edge  # removed 2026-11-07: the candidate (220) is nearer the precomposed glyphs (181)
        },
        0x0066: { # f
            2: (30, -319),  # below anchor
        },
        0x0069: { # i: above on the stem's axis. Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (312, 810),
        },
        0x006A: { # j: above on the stem's axis (the candidate's X is pulled left by the hook). Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (318, 810),
        },
        0x006C: { # l: above and below on the stem's midline, as regular (2026-11-07); the designer's (292, 890) was 20 left, (115, -110) 16 right.
                  # ɫ ɬ ɭ ɮ inherit from it
            0: (312, 890),
            2: (99, -110),
        },
        0x0071: { # q: below at the descender reference, under the stem (2026-11-07), as regular's curated q (386, -319).
                  # Fonts with the anchor at descender depth centre it on the stem (Noto Serif, DejaVu Serif,
                  # Libertinus regular patch and semibold italic designer); those that centre under the bowl
                  # (Gentium, Charis, Andika, Pagella, Junicode, the designer's (169, -110)) put it at the baseline.
                  # The candidate (178, -319) at the lane midline is under neither. X: stem axis (368 at y 0) + Y tan 12.
            2: (300, -319),
        },
        0x0079: { # y: below under the baseline vertex, along the slant, as regular; the designer's
                  # (368, -107) is regular's tucked position, which only suits the dot of ỵ
            2: (240, -319),
        },
        0x00A0: { # no-break space, base for a floating mark, width = 250
            0: (262, 645), # x-height aspect; x = W/2 + Y tan 12
            2: (102, -110),
        },
        0x00C6: { # Æ: above between the macron of Ǣ and the acute of Ǽ, which the designer's (615, 850) misses by 88 and 30
            0: (674, 850),
        },
        0x0122: { # Ģ G cedilla/comma
            0: (513, 850), # G
        },
        0x0141: { # Ł: above as L, on the stem (same outline there); not inherited, the slash lowers the outline match to 56% (2026-11-07)
            0: (314, 850),
        },
        0x014B: { # ŋ eng: above as n's (394, 645), widened with ŋ (2026-11-07). The arch is n's, but the right leg is
                  # 31 further right (mean, y 120-300; stem centres 126 and 370 in n, 126 and 402 in ŋ); n's anchor sits 54%
                  # across its stems, which gives X 411. The designer's (264, 645) is regular's copy, 147 left; the
                  # candidate (382) is pulled left by ŋ's narrower advance width. Semibold italic ŋ needs none: its arch
                  # and legs are n's down to y 210, and its anchor is n's (264, 645).
            0: (411, 645),
        },
        0x0153: { # œ: above over the stroke shared by o and e (2026-11-07), as the designer's œ in the other styles
                  # (regular 405 on 405, semibold 430 on 427, semibold italic 415 on 416); the designer's (480, 645) is æ's, 27 left
            0: (507, 645),
        },
        0x015E: { # S with cedilla
            0: (402, 850),  # S
        },
        0x016B: { # u with macron
            0: (396, 785),  # translated from o with macron
        },
        0x0192: { # f with hook (florin); no designer anchors, stem ~19 deg
            0: (525, 890),  # mark axis 10 left of the apex centre (494) at the apex
            2: (35, -257),  # Y: candidate (tail ends at -172); mark axis 37% from foot (22) to stem (106), as italic f
        },
        # 0x19F: { # O middle tilde
            # 0: (515, 850), # O  # removed 2026-10-29: inherited from O (stage 8): (515, 850)
            # 2: (310, -110) # O  # removed 2026-10-29: inherited from O (stage 8): (311, -110)
        # },
        0x01B1: { # Upsilon
            0: (513, 850), # italic lane
            2: (310, -110), # italic lane
        },
        0x01B2: { # V hook
            0: (506, 850), # italic lane
            2: (302, -110), # italic lane
        },
        0x01B3: { # Y hook
            0: (511, 850), # italic lane of stem
            2: (342, -110), # italic lane of stem
        },
        0x01B5: { # Z stroke
            0: (489, 850), # italic lane
            2: (286, -110), # italic lane
        },
        0x01B7: { # Ezh: above over the caron of Ǯ, which the candidate (485, 850) misses by 55;
                  # below at -319 as in the other styles: at the candidate's -296 five marks overlap
            0: (430, 850),
            2: (236, -319),
        },
        0x0237: { # ȷ dotless j: above on the stem's midline, as j (2026-11-07): j takes this dotless form before nearly every above mark; the designer's (140, 645) was regular's, unslanted, 143 left
            0: (283, 645),
        },
        0x0251: { # ɑ alpha
            2: (197, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x0256: { # ɖ d with tail: redrawn wider than d (bowl 16 left, stem 21 right; stem match 4%), so not inherited (2026-11-06).
                  # X = d's ascender candidate 434 + 4 (centre of bowl and stem) + 2 (slant to Y); Y = 890 + 9 (ascender 707, d 698).
                  # The candidate (465, 899) is pulled right by the wider advance width.
            0: (440, 899),
        },
        0x0258: { # reversed e
            0: (356, 645), # italic anchor model
            2: (202, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x0259: { # schwa
            # 0: (356, 645), # italic anchor model  # removed 2026-10-29: candidate (stage 6) gives (356, 645)
            2: (169, -110), # mark axis through the centre of the bottom of the bowl; designer's (212, -114) was 45 right
        },
        0x025A: { # ɚ schwa with hook
            2: (161, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x025C: { # ɜ reversed open e
            2: (143, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x026D: { # ɭ l with retroflex hook
            0: (312, 890),  # above over the stem midline, as l should be (l itself is 20 left of its stem) (2026-11-07)
        },
        0x026E: { # ɮ: below ʒ's below anchor (130) + the shift of the ezh (+77 at its bowl; redrawn, 77-106), as regular (2026-11-07)
            2: (207, -319),
        },
        0x0270: { # ɰ turned m with long leg: under the middle stem (2026-11-06); width differs from ɯ, so not derived.
                   # X = middle-stem centre + Y tan 12; Y = ɯ's candidate (same arches); no below mark collides
            2: (362, -123),
        },
        0x0276: { # ɶ: above over the stroke shared by the o and the E, regular's method (2026-11-07)
            0: (468, 645),
            2: (308, -110),  # below under the stroke shared with the E, as regular (2026-11-07)
        },
        0x0279: { # ɹ: above over the stem top, regular's method (2026-11-07)
            0: (275, 645),
        },
        0x027A: { # ɺ: above over the stem at the ascender reference, as regular (2026-11-07)
            0: (456, 890),
        },
        0x027B: { # ɻ turned r with hook
            0: (389, 645),  # above over the stem midline, as ɹ; not inherited (stem match 58%), the candidate (352) was 37 left (2026-11-07)
        },
        0x027C: { # ɼ r with long leg: below on the stem's axis, at the descender reference
            2: (53, -319),
        },
        0x027E: { # ɾ: below under the stem, as r (2026-11-07)
            2: (104, -110),
        },
        0x0280: { # ʀ: above as R: R's patched offset from the centre of its upper ink, scaled by the widths, regular's method (2026-11-07)
            0: (346, 645),
        },
        0x0283: { # ʃ: below under the stem, at the descender reference (2026-11-07)
            2: (61, -319),
        },
        0x028A: { # upsilon
            # 0: (358, 645), # italic lane  # removed 2026-11-07: old italic-lane value; the candidate implements the italic model
            # 2: (267, -110), # italic lane  # removed 2026-11-07: old italic-lane value; the candidate implements the italic model
        },
        0x028C: { # ʌ: below centre of the gap between the feet, as regular (2026-11-07)
            2: (210, -110),
        },
        0x028D: { # ʍ turned w: below centred on the middle foot, not the bbox midpoint
            2: (361, -110),
        },
        0x028E: { # ʎ: above over the apex of the turned V, at the ascender reference, as regular (2026-11-07)
            0: (442, 890),
        },
        0x0293: { # ʓ ezh with curl
            2: (133, -399),  # below: ymin -312 minus the descender clearance (87), no overshoot correction (the curl is sharp); X the candidate's (ʒ matches 26-35%) (2026-11-07)
        },
        0x0294: { # glottal stop, top 672: above the capline
            0: (376, 867), # 850 + 27 - 10 (bowl overshoot); x = W/2 + Y tan 12
        },
        0x0295: { # pharyngeal, top 683: above the capline
            0: (379, 878), # 850 + 38 - 10 (bowl overshoot); x = W/2 + Y tan 12
        },
        0x0299: { # ʙ: above as B: B's patched offset from the centre of its upper ink, scaled by the widths, regular's method (2026-11-07)
            0: (371, 645),
        },
        0x029F: { # ʟ: above over the stem, as L, regular's method (2026-11-07)
            0: (277, 645),
        },
        0xE100: { # en space with anchor, width = 320
            0: (160, 645),
            2: (160,-110),
        },
    },
    "marks": {
        # Tall below marks (2026-11-08): anchor moved up so that the mark rises at most 62 above it,
        # as U+0329 and U+0348; they overlapped descenders at -319 and crowded baseline letters
        # (report, "Mark anchor model", stage 7). x unchanged.
        0x0318: { # left tack below
            2: (-254, -118), # was (-254, -148)
        },
        0x0319: { # right tack below
            2: (-315, -117), # was (-315, -147)
        },
        0x031C: { # left half ring below
            2: (-246, -114), # was (-246, -146)
        },
        0x031F: { # plus sign below
            2: (-278, -115), # was (-278, -145)
        },
        0x0339: { # right half ring below
            2: (-246, -114), # was (-246, -146)
        },
        0x0325: { # ring below
            2: (-242, -96), # was (-242, -116); the precomposed Ḁ ḁ put the ring here (within 2)
        },
        0x034E: { # upwards arrow below
            2: (-249, -90), # was (-249, -110)
        },
        0x030B: { # double acute above
            0: (-57, 714), # -52 = x-mid of bbox, with -5 offset for acute weght
        },
        0x0330: { # tilde below
            2: (-220, -70), # x-mid of bbox
        },
    },
    "marks_by_name": {
        # Italic .cap anchors fitted to the precomposed capitals (2026-11-07): each X is moved so that the
        # accent's centre lands, as a median over the capitals, where the designer drew it in the
        # precomposed glyph (as in regular, where every .cap mark is within a few units of them).
        # Stage 4 and the earlier curated values left the symmetric marks about 14 left of the
        # precomposed accents and the caron about 15 right. Measured after italic O, U, Y were set
        # from their precomposed glyphs. Dieresis, dot above, hook above were within 4: stage 4 kept.
        "grave.cap": {
            0: (-6, 724),    # median +39 from (-45, 724), the earlier "scaled from regular"; graves vary by letter (+8..+89)
        },
        "acute.cap": {
            0: (-50, 724),   # median -13 from stage 4's (-37, 724); acutes vary by letter (-78..+25)
        },
        "circumflex.cap": {
            0: (15, 683),    # median -9 from stage 4's (24, 683)
        },
        "breve.cap": {
            0: (-14, 702),   # median -12 from stage 4's (-1, 702)
        },
        "caron.cap": {
            0: (-32, 677),   # median +18 from (-50, 677), the earlier "x vertex", which ignored the slant
        },
#        "dotaccent.cap" no such italic glyph
        # "dieresis.cap": {
            # 0: (-75, 857), # xmid, y implied. test x  # removed 2026-10-29: stage 4 gives (-69, 857)
        # },
        # "hookabovecomb.cap": {
            # 0: (-27, 811) # x apex, y implied  # removed 2026-10-29: stage 4 gives (-19, 816)
        # },
        "hungarumlaut.cap": {
            0: (-109, 762),  # median -6 from stage 4's (-103, 762); only Ő Ű
        },
        "uni030F.cap": { # double grave
            0: (-40, 766),   # median +7 from (-47, 766)
        },
        "breveinvertedcmb.cap": {
            0: (-12, 703),   # median +10 from (-23, 703)
        },
    },    
}
