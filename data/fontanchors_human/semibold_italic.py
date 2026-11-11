# Anchor data
# 0 above. 2 below

anchors = {
    "bases": {
        # Dotted i letters: above as i (2026-11-08); marks that keep the dot (all marks on į ị, U+033F on ɨ) crowded it
        0x012F: { # į
            0: (180, 823), # was (132, 775)
        },
        0x1ECB: { # ị
            0: (180, 823), # was (132, 775)
        },
        0x0268: { # ɨ
            0: (180, 823), # was (137, 795)
        },
        0x0049: { # I: below on the stem's axis (179 at y 0), plus 12 (K below) (2026-11-07). The designer's (147, -110),
                  # regular's copy, is 22 left of it; the candidate (161, -110) 8 left
            2: (169, -110),
        },
        0x004C: { # L: above on the stem's axis, less K = 150 (2026-11-07), where the designer centred the acute of Ĺ (8 left)
            0: (209, 850),
        },
        0x0055: { # U: above on the letter's axis, as italic V (2026-11-07): marks shaped with dot, macron, circumflex land on it (the midline between the stems); the designer's (346, 850), regular's, put them 30 left
            0: (376, 850),
        },
        0x0056: { # V: above on the letter's axis, as italic V (2026-11-07): marks shaped with dot, macron, circumflex land on it (the bisector of the arms); the designer's (336, 850), regular's, put them 23 right
            0: (313, 850),
        },
        0x0059: { # Y
            # 0: (319, 850), # italic lane - K (150): semibold italic model  # replaced 2026-11-07: marks 28 right of the arms' bisector
            0: (291, 850), # on the bisector of the upper arms, as italic V, U, Y (2026-11-07): shaped marks land on it
            2: (277, -110) # italic lane
        },
        0x0061: { # a
            # 0: (340, 645),  # test was (379,645)
            # 2: (277, -110),  # x-mid of (78,132) to (475,132) on right edge  # removed 2026-11-07: the candidate (260) is nearer the precomposed glyphs (248)
        },
        0x0066: { # f
            2: (62, -319),  # below anchor
        },
        0x0069: { # i: above on the stem's axis less K = 150. Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (180, 823),
        },
        0x006A: { # j: above on the stem's axis less K = 150 (the candidate's X is pulled left by the hook). Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (197, 823),
        },
        0x006C: { # l: above and below on the stem's midline (less K = 150 above, plus 12 below), as regular (2026-11-07); the designer's (174, 890) was 6 left; (135, -110) was regular's.
                  # ɫ ɬ ɭ ɮ inherit from it
            0: (180, 890),
            2: (138, -110),
        },
        0x00A0: { # no-break space, base for a floating mark, width = 274
            0: (118, 645), # x-height aspect; x = W/2 + Y tan 11.5 - K
            2: (127, -110),
        },
        0x00C6: { # Æ: above between the macron of Ǣ and the acute of Ǽ, which the designer's (500, 850) misses by 75 and 16
            0: (545, 850),
        },
        0x0122: { # Ģ G cedilla/comma
            # 0: (383, 850), # G  # removed 2026-11-10: 18 right of G's anchor in Ģ; stage 9 inherits G's (365, 850)
        },
        0x0134: { # Ĵ: below, the semibold italic candidate from Ĵ's own metrics (2026-11-10): W 340, ymin -196 (d+36),
                  # by = -319 + 36 + 2 = -281, bx = W/2 + by tan θ + 12 = 125. Stage 9 cannot inherit J's: the stem was
                  # redrawn (Ĵ has a flat top serif, J the italic swash) and the tail is deeper (-196, J -164) (match 64%)
            2: (125, -281),
        },
        0x015E: { # S with cedilla
            # 0: (232, 850),  # S  # removed 2026-11-10: stage 9 inherits S's, 1 left (231, 850)
        },
        0x0186: { # Ɔ open O: above over the bowl, 24 left of the outline's axis (2026-11-08), so marks land as in
                  # regular (curated, 32 left) and semibold (designer, 39 left). The stage 6 candidate (357, 850)
                  # was 20 right of the axis (the ink sits left in its advance) and put marks visibly right.
            0: (313, 850),
        },
        0x018F: { # Schwa
            0: (335, 850), # mark axis through the centre of the top of the arc, - K (candidate 369 was 34 right)
        },
        0x0190: { # open-E
            # 0: (256, 850), # italic lane  # removed 2026-11-07: old italic-lane value; the candidate implements the semibold italic model
        },
        0x0192: { # f with hook (florin); no designer anchors, stem ~19 deg
            0: (386, 890),  # mark axis 10 left of the apex centre (507) at the apex, - K (150)
            2: (60, -255),  # Y: candidate (tail ends at -170); mark axis 37% from foot (34) to stem (118), - K (-12)
        },
        # 0x19F: { # O middle tilde
            # 0: (335, 850), # O  # removed 2026-10-29: inherited from O (stage 8): (335, 850)
            # 2: (350, -110), # O   # removed 2026-10-29: inherited from O (stage 8): (350, -110)
        # },
        # ư and its toned forms Ứ Ừ Ử Ữ (which reference ư at (0, 0)): below as u's (270, -110), shift 0 (2026-11-10; u's was 239 until it was deleted).
        # Stage 9 cannot inherit it: ư's stems lie on u's (shift 0 left, +1 right), but the bottom of the bowl was
        # redrawn about 15 wider on each side around the same midpoint (306, u 307), so the fit is 75%.
        # ự has a dot below and needs no below anchor.
        0x01B0: {2: (270, -110)},  # ư
        0x01A1: { # ơ: below on the hornless advance lane (2026-11-10). Without the horn the ink ends at x 527; with o's
                  # sidebearings (72, -10) the lane is 517 wide: 517/2 - 110 tan θ + 12 = 248. The designer's 243 was 4 left of
                  # what Ớ Ờ Ở Ỡ inherit (247); the candidate from ơ's own advance (541, horn included) is 260
            2: (248, -110),
        },
        0x1EE9: {2: (270, -110)},  # ứ
        0x1EEB: {2: (270, -110)},  # ừ
        0x1EED: {2: (270, -110)},  # ử
        0x1EEF: {2: (270, -110)},  # ữ
        0x01B1: { # Upsilon
            0: (356, 850), # italic lane - K (150): semibold italic model
            2: (311, -110), # italic lane
        },
        0x01B2: { # V hook
            0: (348, 850), # italic lane - K (150): semibold italic model
            2: (303, -110) # italic lane
        },
        0x01B3: { # Y hook
            0: (391, 850), # italic lane of stem - K (150): semibold italic model
            2: (379, -110) # italic lane of stem
        },
        0x01B5: { # Z stroke
            0: (312, 850), # italic lane - K (150): semibold italic model
            2: (267, -110) # italic lane
        },
        # Redrawn derived letters that cannot inherit by outline match: anchors on the geometric centre of their major
        # strokes, measured in sheared coordinates and carried up the slant to the anchor's height (2026-11-10)
        0x0289: { # ʉ: midline of the two stems (294 at y 0, below the bar), less K (150 above, -12 below); the lane was pulled by the bar
            0: (275, 645),
            2: (284, -110),
        },
        0x027D: { # ɽ: above midway between the stem (142) and the ball (333), less K = 150; the slab serif and tail do not count
            0: (218, 645),
        },
        # 0x2C64: { # Ɽ (removed 2026-11-10: stage 6's advance lane differs by 1-7; Ɽ is in BASE_LATIN): above on the lane of its P part without serifs (68..487), less K = 150
        #     0: (300, 850),
        # },
        0x0290: { # ʐ: above on the midline of the top bar (103..422), less K = 150; the hook does not count
            0: (244, 645),
        },
        0x0291: { # ʑ: above on the midline of the top bar (60..407), less K = 150; the curl does not count
            0: (215, 645),
        },
        0x0237: { # ȷ dotless j: above on the stem's midline, as j (2026-11-07): j takes this dotless form before nearly every above mark, less K = 150; the designer's (140, 645) was regular's, 31 left
            0: (171, 645),
        },
        0x0251: { # ɑ alpha
            2: (225, -110),  # below under the lowest point of the bowl, as ə (2026-11-07), plus 12 (K below)
        },
        0x0258: { # ɘ reversed e
            2: (201, -110),  # below under the lowest point of the bowl, as ə (2026-11-07), plus 12 (K below)
        },
        0x0259: { # schwa
            2: (186, -110), # mark axis through the centre of the bottom of the bowl, - K (candidate 227 was 41 right)
        },
        0x025A: { # ɚ schwa with hook
            2: (188, -110),  # below under the lowest point of the bowl, as ə (2026-11-07), plus 12 (K below)
        },
        0x025C: { # ɜ reversed open e
            2: (193, -110),  # below under the lowest point of the bowl, as ə (2026-11-07), plus 12 (K below)
        },
        0x026D: { # ɭ l with retroflex hook
            0: (205, 890),  # above over the stem midline, less K = 150 (2026-11-07)
        },
        0x026E: { # ɮ: below ʒ's below anchor (141) + the shift of the ezh (+90), as regular, plus 12 (K below) (2026-11-07)
            2: (231, -319),
        },
        0x0270: { # ɰ turned m with long leg: under the middle stem (2026-11-06); width differs from ɯ, so not derived.
                   # X = middle-stem centre + Y tan 11.5 + 12 (K below) = 388, less 2: at 388 U+034D also collides; Y = ɯ's candidate (same arches);
                   # no below mark collides except U+0347
            2: (386, -110),
        },
        0x0276: { # ɶ: above over the stroke shared by the o and the E less K = 150, regular's method (2026-11-07)
            0: (327, 645),
            2: (336, -110),  # below under the stroke shared with the E, as regular, plus 12 (K below) (2026-11-07)
        },
        0x0279: { # ɹ: above over the stem top less K = 150, regular's method (2026-11-07)
            0: (211, 645),
        },
        0x027A: { # ɺ: above over the stem at the ascender reference, less K = 150, as regular (2026-11-07)
            0: (313, 890),
        },
        0x027C: { # ɼ r with long leg: below on the stem's axis, at the descender reference
            2: (78, -319),
        },
        0x027E: { # ɾ: below under the stem, as r, plus 12 (K below) (2026-11-07)
            2: (132, -110),
        },
        0x0280: { # ʀ: above as R: R's patched offset from the centre of its upper ink, scaled by the widths less K = 150, regular's method (2026-11-07)
            0: (206, 645),
        },
        0x0283: { # ʃ: below under the stem, at the descender reference, plus 12 (K below) (2026-11-07)
            2: (88, -319),
        },
        0x028A: { # upsilon
            # 0: (219, 645), # italic lane - K (150): semibold italic model  # removed 2026-11-07: old italic-lane value; the candidate implements the semibold italic model
            # 2: (281, -110), # italic lane  # removed 2026-11-07: old italic-lane value; the candidate implements the semibold italic model
        },
        0x028C: { # ʌ: below centre of the gap between the feet, as regular, plus 12 (K below) (2026-11-07)
            2: (209, -110),
        },
        0x028D: { # ʍ turned w: below centred on the middle foot, not the bbox midpoint
            2: (369, -110),
        },
        0x028E: { # ʎ: above over the apex of the turned V, at the ascender reference, less K = 150, as regular (2026-11-07)
            0: (286, 890),
        },
        0x0292: { # ʒ: above, the candidate's X (211; the designer's 218 was regular's) at the x-height reference, as ʒ in
                  # the other styles: the candidate's Y (667) is raised by the top's 14-unit overshoot (2026-11-07)
            0: (211, 645),
        },
        0x0293: { # ʓ: above as ʒ's above anchor, at ʒ's Y; the tops match within a few units less K = 150, regular's method (2026-11-07)
            0: (213, 645),  # follows ʒ's candidate (211) + 2 (2026-11-07)
            2: (157, -415),  # below: ymin -328 minus the descender clearance (87), no overshoot correction (the curl is sharp); X the candidate's (ʒ matches 39-56%) (2026-11-07)
        },
        0x029F: { # ʟ: above over the stem, as L less K = 150, regular's method (2026-11-07)
            0: (137, 645),
        },
    },
    "marks": {
        # Above marks moved vertically by Delta y (2026-11-09): the median offset, composed (base + CGJ + mark)
        # minus the designer's precomposed glyphs, on x-height bases, where it is the same (within a few units)
        # on every base. A positive Delta y raises the anchor by that much, so the mark sits that much lower.
        # X moves with the slant (by Delta y tan theta) so that the mark stays on its axis: k is unchanged, within
        # 10 of the mark-axis rule (k = K). In regular and semibold X is unchanged.
        0x0304: { # macron
            0: (-216, 613), # was (-209, 645); Delta y -32 (ā ē ī ō ȳ, -32; the precomposed macron is drawn 32 higher)
        },
        0x0307: { # dot above
            0: (-178, 678), # was (-180, 667); Delta y +11 (ċ ė ġ ż ȧ ṁ ṅ …, +11 to +12)
        },
        0x030A: { # ring above
            0: (-179, 731), # was (-184, 708); Delta y +23 (å ẙ +23, ẘ +16)
        },
        0x030B: { # double acute
            0: (-217, 725), # was (-219, 714); Delta y +11 (ő)
        },

        # Tall below marks (2026-11-08): anchor moved up so that the mark rises at most 62 above it,
        # as U+0329 and U+0348; they overlapped descenders at -319 and crowded baseline letters
        # (report, "Mark anchor model", stage 7). x unchanged.
        0x0318: { # left tack below
            2: (-224, -118), # was (-224, -148)
        },
        0x0319: { # right tack below
            2: (-285, -118), # was (-285, -147)
        },
        0x031C: { # left half ring below
            2: (-216, -114), # was (-216, -146)
        },
        0x031F: { # plus sign below
            2: (-249, -116), # was (-249, -145)
        },
        0x0339: { # right half ring below
            2: (-216, -114), # was (-216, -146)
        },
        0x0325: { # ring below
            2: (-218, -96), # was (-218, -116); the precomposed Ḁ ḁ put the ring here (within 2)
        },
        0x034E: { # upwards arrow below
            2: (-227, -90), # was (-227, -110)
        },
        # Removed: the designer's grave (-142, 683) and double acute (-219, 714)
        # fit the semibold italic model. These lacked K and landed the marks
        # 142 and 190 units left; they had been fitted to a, whose above-anchor
        # carried the slant (now deleted in stage 1 and refilled by stage 6).
        # 0x0300: { # grave
        #     0: (0, 683), # was (-142, 683)
        # },
        # 0x030B: { # double acute above
        #     0: (-28, 719),  # -23 = x-mid of bbox, with -5 left offset for acute weight
        # },
        0x0330: { # tilde below
            2: (-196, -70), # x-mid of bbox
        },
        0x0331: { # macron below: the outline is semibold's (y -79..-35) but the anchor was regular's (-244, -110),
                  # 75 below the outline's top instead of 23 as in every other style, so the mark sat 52 higher
                  # (gap to n 25, against 86-96 in the other styles). Y = top - 23, as semibold;
                  # X + 52 tan 11.5 to stay on the axis (2026-11-06). The precomposed glyphs put it only 27 lower.
            2: (-233, -58),
        },
        # Mark-axis snap (2026-11-06): X = C + Y tan 11.5 + d - 150, d = regular's
        # offset from the axis; checked against the precomposed glyphs
        # (median distance of the mark from them, before -> after).
        0x0309: { # hook above
            0: (-142, 765), # was (-160, 765); precomposed 26 -> 8 (5 glyphs)
        },
        0x0311: { # inverted breve
            0: (-223, 645), # was (-205, 645); precomposed 19 -> 3 (5 glyphs)
        },
        0x0314: { # reversed comma above
            0: (-91, 605), # was (-76, 605); precomposed 19 -> 4 (1 glyph)
        },
    },
    "marks_by_name": {
        # Removed 2026-11-08: acute.cap (-236, 723), grave.cap (-194, 724),
        # hungarumlaut.cap (-282, 762), uni030F.cap (-214, 767), curated on
        # 2026-11-06 at the mark-axis position (C + Y tan θ + d − K, d from regular).
        # Stage 4 applies instead (-195, -168, -243, -167): it fits the accents to the
        # designer's precomposed capitals, so composed capitals without a precomposed
        # form match the precomposed ones in the same text. The curated values fitted
        # only the designer's original capital anchors; with H I J K L N O U V Y Æ moved
        # on 2026-11-07, stage 4 is closer to the precomposed glyphs (median 10/30/6/15
        # against 32/30/45/37 for grave/acute/double acute/double grave).
    },
    "bases_by_name": {
        "uni027F.desc": {  # ɿ with descender, U+E27F, added in stage 2 (2026-11-09): below under the stem's centre
                            # (stem 99-218 at y -319, centre 158, plus 12 (K below)) at the descender reference, as q; above is inherited from ɿ in stage 8
            2: (170, -319),
        },
    },
}
