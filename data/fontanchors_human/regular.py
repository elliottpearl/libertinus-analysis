# Anchor data, set by human operator
"""
anchor class index 0 above
    superscript capitals from compute_baseanchor0()

anchor class index 1 above-right

anchor class index 2 below

anchor class index 3 above-right (left-angle)
    superscript capitals
        test 2 values computed with compute_baseanchor3(), clearance 0/80. Rejected.
        test 3 values computed with compute_baseanchor3(), clearance -20/70. Accepted.

TODO: delete any human anchor for AE, Ezh and any letter whose only expected combinations are precomposed.        
"""

anchors = {

    "bases": {
        # Dotted i letters: above as i (2026-11-08); marks that keep the dot (all marks on į ị, U+033F on ɨ) crowded it
        0x012F: { # į
            0: (142, 834), # was (132, 825)
        },
        0x1ECB: { # ị
            0: (142, 834), # was (132, 775)
        },
        0x0268: { # ɨ
            0: (142, 834), # was (155, 795)
        },
        0x0041: {  # A; designer's (354, 850), (308, -110) are left of the midline
            0: (361, 850),  # centre of the cut apex, x 334..389
            2: (339, -110), # centre between the serif feet, 115.5 and 562.5; Ạ has 338
        },
        # 0x004A: {  # J
            # 2: (109, -254), # was (109, -319), not full descender, heristic clearance gives y = -272  # removed 2026-10-30: trying the candidate (stage 6)
        # },
        # 0x0051: {  # Q
            # 2: (350, -291), # -309  # removed 2026-10-29: candidate (stage 6) gives (359, -294)
        # },
        0x0062: {  # b
            0: (279, 885),  # apex of bowl
        },
        0x0063: {  # c
            # 2: (227, -110),  # removed 2026-11-07: within 10 of the candidate
        },
        0x0064: {  # d
            0: (235, 885), # xmid of bowl counter; ascender aspect.
            # 2: (222, -110), # xmid of bowl extrema; baseline aspect.
            2: (235, -110), # xmid of bowl counter; ascender aspect.
        },
        0x0066: {  # f
            0: (273, 885),  # apex of f
            2: (136, -110),
        },
        0x0068: {  # h
            0: (282, 885),  # center of stems + offset
        },
        0x0069: { # i: above on the stem's axis. Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (142, 834),
        },
        0x006A: { # j: above on the stem's axis (the candidate's X is pulled left by the hook). Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (152, 834),
        },
        # 0x006A: {  # j
            # 0: (126, 795),  # shifted by 11 from i  # removed 2026-11-07: 26 left of the stem; U+033F 16 above the dot
        # },
        0x006B: {  # k
            0: (272, 885),  # center of < part + offset
            # 2: (290, -110),  # removed 2026-11-07: the candidate (261) is nearer the precomposed glyphs (258)
        },
        0x006D: {  # m
            # 2: (404, -110),  # removed 2026-11-07: within 2 of the candidate
        },
        0x0070: {  # p
            2: (120, -319),
        },
        0x0071: {  # q
            2: (386, -319),
        },
        0x0072: {  # r
            2: (140, -110),
        },
        0x0074: {  # t
            0: (139, 769),  # apex center; ascender clearance
        },
        # 0x007A: {  # z
            # 0: (220, 645),  # removed 2026-10-29: designer's anchor is (220, 646)
        # },
        0x00A0: { # no-break space, base for a floating mark, width = 250
            0: (125, 645), # x-height aspect; x = W/2
            2: (125, -110),
        },
        0x00C0: { # A grave
            2: (308,-110), # A anchor below
        },
        0x00C1: { # Á A acute
            2: (308,-110), # A anchor below
        },
        0x00C6: { # Æ: above between the macron of Ǣ and the acute of Ǽ, which the designer's (480, 850) misses by 81 and 68
            0: (555, 850),
        },
        # 0x00C8: { # E grave
        #    2: (287, -110), # E below anchor
        # },
        0x00C9: { # É E acute
            2: (287, -110), # E below anchor
        },
        0x00CC: { # I grave
            2: (147,-110),  # I below anchor
        },
        0x00CD: { # Í I acute
            2: (147,-110),  # I below anchor
        },
        0x00D9: { # U grave
            2: (328,-110),  # U below anchor
        },
        0x00DA: { # Ú U acute
            2: (328,-110),  # U below anchor
        },
        0x00E0: { # a grave
            2: (196, -110),
        },
        0x00E1: { # á a acute
            2: (196, -110),
        },
        # 0x00E6: {  # æ ae ligature
            # 0: (350, 645),  # removed 2026-10-29: designer's anchor is (350, 645)
            # 2: (327, -110),  # removed 2026-10-29: designer's anchor is (327, -109)
        # },
        0x00E8: { # e grave
            2: (234, -110),
        },
        0x00E9: { # é e acute
            2: (234, -110),
        },
        0x00EC: { # i grave
            2: (136, -110),
        },
        0x00ED: { # í i acute
            2: (136, -110),
        },
        # 0x00F2: { # o grave
        #     2: (243, -110),
        # },
        # 0x00F3: { # ó o acute
        #    2: (243, -110),
        # },
        0x00F9: { # u grave
            2: (239, -110),
        },        
        0x00FA: { # ú u acute
            2: (239, -110),
        },        
        0x011A: { # Ě E caron
            2: (287,-110),
        },
        0x011B: { # ě e caron
            2: (234,-110),
        },
        0x0122: { # Ģ G cedilla/comma
            0: (365, 850), # G
        },
        0x014B: {  # ŋ eng
            2: (265, -319),  # descender reference; X n's below anchor (265): ŋ's legs are n's from the stem foot up, shift 0 (confirmed 2026-11-07)
        },
        0x0153: {  # œ oe ligature
            2: (408, -110),  # center of vertical band
        },
        0x015E: { # S with cedilla
            0: (232, 850),  # S
        },
        0x0170: { # Ű U double acute
            2: (328, -110),
        },
        0x0171: { # ű u double acute
            2: (239, -110),
        },
        0x0186: { # Ɔ open O
            0: (290, 850), # xmid bowl, capital aspect
            2: (294, -110), # xmid bowl, baseline aspect
        },
        0x018F: { # Schwa
            0: (306,850), # centre of the top of the arc (was 327, bbox x mid, 21 right)
            # 2: (316,-110) # ymin  # removed 2026-11-07: within 10 of the candidate
        },
        # 0x0190: {  # Ɛ open E
            # 0: (248, 850),  # xmid bbox, capital aspect  # removed 2026-10-29: candidate (stage 6) gives (256, 850)
            # 2: (248, -110),  # removed 2026-10-29: candidate (stage 6) gives (256, -110)
        # },
        0x0192: {  # f with hook (florin), drawn like italic f with a ~7 deg stem
            0: (323, 885),  # apex, as f: 10 left of the apex centre (333)
            2: (84, -319),  # as italic f: between foot (53) and stem (138), 37% from the foot
        },
        # 0x19F: { # O middle tilde
            # 0 : (335, 850), # O  # removed 2026-10-29: inherited from O (stage 8): (335, 850)
        # },
        0x01A9: { # Esh
            0: (268, 850), # xm above
            2: (277, -110), # xm below
        },
        0x01B1: { # Upsilon
            0: (329, 850), # xm above
            2: (327, -110), # ymin
        },
        0x01B2: { # V hook
            0: (369, 850), # xm above
            2: (324, -110) # ymin
        },
        0x01B3: { # Y hook
            0: (295, 850), # Y
            2: (295, -110) # Y
        },
        0x01B5: { # Z stroke
            0: (320, 850), # Z
            2: (287, -110) # Z
        },
        # 0x01B7: { # Ezh
            # 0: (307, 850), # xm above  # removed 2026-10-29: candidate (stage 6) gives (303, 850)
        # },
        0x01CD: { # Ǎ A caron
            2: (308,-110),
        },
        0x01CE: { # ǎ a caron
            2: (196,-110),
        },
        0x01CF: { # Ǐ I caron
            2: (147,-110),
        },
        0x01D0: { # ǐ i caron
            2: (136,-110),
        },
        # 0x01D1: { # Ǒ O caron
        #    2: (350,-110),
        # },
        0x01D2: { # ǒ o caron
            2: (243,-110),
        },
        0x01D3: { # Ǔ U caron
            2: (328,-110),
        },
        0x01D4: { # ǔ u caron
            2: (239,-110),
        },
        0x0200: { # Ȁ A double grave
            2: (308, -110),
        },
        0x0201: { # ȁ a double grave
            2: (196, -110),
        },
        0x0204: { # Ȅ E double grave
            2: (287, -110),
        },
        0x0205: { # ȅ e double grave
            2: (234, -110),
        },
        0x0208: { # Ȉ I double grave
            2: (147, -110),
        },
        0x0209: { # ȉ i double grave
            2: (136, -110),
        },
        # 0x020C: { # Ȍ O double grave
        #    2: (350, -110),
        # },
        # 0x020D: { # ȍ o double grave
        #    2: (243, -110),
        # },
        0x0214: { # Ȕ U double grave  
           2: (328, -110),
        },
        0x0215: { # ȕ u double grave  
           2: (239, -110),
        },
        0x0237: { # dotless j
            0: (152, 645),  # above on the stem's midline, as j (2026-11-07): j takes this dotless form before nearly every above mark; the designer's (140, 645) was 12 left
            2: (109, -319), # j
        },
        0x023F: {  # ȿ s-swash-tail
            2: (196, -283),  # ymin + meanline anchor
        },
        0x0250: {  # ɐ turned-a
            # 2: (229, -110),  # removed 2026-11-07: no reason recorded; the candidate (216) is 13 away
        },
        0x0251: {  # ɑ alpha
            # 2: (222, -110),  # replaced 2026-11-07
            2: (248, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x0252: {  # ɒ turned-alpha
            # 2: (259, -110),  # removed 2026-11-07: no reason recorded; the candidate (247) is 12 away
        },
        0x0253: {  # ɓ b-hook
            # 0: (255, 885),  # x at ymax  # removed 2026-11-07: ɓ inherits from b (derived_y), as in the other styles
            # 2: (235, -110),  # x at ymin  # removed 2026-10-29: inherited from b (stage 8): (240, -110)
        },
        # 0x0257: { # ɗ d-hook
        #     0: (218, 885),
        # },  # removed 2026-11-06: no reason recorded, 17 left of d's (235, 885); stage 8 inherits from d
        0x0258: { # ɘ reversed e
            2: (183, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x0259: { # schwa; designer's (195, 645), (186, -114) are 24 and 26 left
            0: (219, 645),  # centre of the top of the arc
            2: (212, -110), # centre of the bottom of the bowl
        },
        0x025A: { # ɚ schwa with hook
            2: (184, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x0260: {  # ɠ g-hook
            # 0: (239, 885),  # matches 0x0261  # removed 2026-11-07: stage 8 (derived_y) gives ɡ's X at 885
            2: (226, -319),
        },
        0x0263: {  # ɣ gamma
            # 2: (248, -289),  # ymin -87  # removed 2026-11-07: within 10 of the candidate
        },
        0x0266: {  # ɦ h-hook
            # 0: (263, 885),  # apex of arm  # removed 2026-11-07: the candidate is the same
            # 2: (262, -110),  # center of counter  # removed 2026-11-07: the candidate is the same
        },
        0x026B: {  # ɫ l-tilde
            # 0: (225, 885),  # center of l  # removed 2026-11-07: ɬ's value (its l is 88 right); ɫ inherits from l (+12), 147
            # 2: (225, -110),  # removed 2026-11-07: as above
        },
        # 0x026C: {  # ɬ l-belt
            # 0: (225, 885),  # center of l  # removed 2026-10-29: inherited from l (stage 8): (223, 885)
            # 2: (225, -110),  # removed 2026-10-29: inherited from l (stage 8): (223, -110)
        # },
        # 0x026D: {  # ɭ l-hook
        # 2: (196, -275),  # ymin = -188 → -275
        # },  # removed 2026-11-06: stage 8 gives X from l's stem (133) and Y the candidate; 1 below mark collides there, 4 here
        0x026E: {  # ɮ lezh
            # 0: (135, 885),  # center of l  # removed 2026-11-07: stage 8 inherits from l (137, 885)
            2: (275, -319),  # below ezh anchor
        },
        0x0270: { # ɰ turned m with long leg: under the middle stem (2026-11-06); width differs from ɯ, so not derived.
                   # X = middle-stem centre; Y = ɯ's candidate (same arches); no below mark collides
            2: (378, -121),
        },
        # 0x0273: {  # ɳ n-retroflex-hook
        # 2: (262, -308),  # -319 + 11
        # },  # removed 2026-11-06: stage 8 gives (255, -306): X from n, Y the candidate
        # 0x0275: {  # ɵ barred-o
            # 0: (238, 645),  # x from o  # removed 2026-10-29: inherited from o (stage 8): (238, 645)
            # 2: (243, -110),  # removed 2026-10-29: inherited from o (stage 8): (243, -110)
        # },
        0x0276: {  # ɶ OE ligature
            0: (361, 645),  # center of lig band
            2: (361, -110),
        },
        0x0279: { # ɹ: above over the stem top (188-267), mirroring r's below anchor on r's stem; the candidate (178) is pulled left
                  # by the arm at the bottom (2026-11-07; the designer's was a's (209, 645))
            0: (227, 645),
        },
        0x027A: {  # ɺ turned-r-long-leg
            0: (232, 885),  # ascender aspect; X over the stem (2026-11-07; was 208, 23 left of it)
        },
        0x027B: {  # ɻ turned-r-hook
            0: (248, 645),  # center of stem (2026-11-07: measured 209-286; was 238, 10 left)
        },
        0x027C: { # ɼ r with long leg: below on the stem's axis, at the descender reference
            2: (134, -319),
        },
        0x027E: { # ɾ: below under the stem, as r's below anchor; the designer's was a's (196, -110) (2026-11-07)
            2: (126, -110),
        },
        0x0280: { # ʀ: above as R's: R's (269, 850) is 3 left of the centre of its upper ink (y > 330); ʀ's centre (y > 215) is 228,
                  # and 3 scaled by the widths (473/587) is 2 (2026-11-07; the designer's was a's (209, 645))
            0: (226, 645),
        },
        # 0x0282: {  # ʂ s-hook
        # 2: (196, -263),  # ymin -87
        # },  # removed 2026-11-06: stage 8 gives (190, -261): X from s, Y the candidate
        0x0283: {  # ʃ esh
            2: (129, -319),  # descender aspect; X under the stem (2026-11-07; was 209, a's above X copied)
        },
        0x028A: { # upsilon
            # 0: (253, 645), # xm  # removed 2026-11-07: within 1 of the candidate
            # 2: (253, -110), # xm  # removed 2026-11-07: within 1 of the candidate
        },
        0x028C: {  # ʌ turned-v
            # 0: (249, 645),  # vertex  # removed 2026-11-07: within 5 of the candidate
            2: (229, -110),  # center of serifs
        },
        0x028D: { # ʍ turned w: below centred on the middle foot, not the bbox midpoint
            2: (378, -110),
        },
        0x028E: {  # ʎ turned-y
            0: (242, 885),  # ascender aspect; X over the apex of the turned V, mirroring y's below anchor (242) (2026-11-07; was a's 209)
        },
        0x0293: { # ʓ: above as ʒ's (218, 645) plus the outline shift (+4); not inherited, the stem match finds no stems in an ezh (38%) (2026-11-07; the designer's was a's (209, 645))
            0: (222, 645),
        },
        0x0297: { # ʗ: above as c's (242, 645), whose top it shares, plus the shift of the top (+10, crossings at y 300-400)
                  # (2026-11-07; the designer's was a's (209, 645)). Only in regular: the other styles drew ʗ's top wider than c's
            0: (252, 645),
        },
        0x0299: { # ʙ: above as B's: B's (267, 850) is 4 right of the centre of its upper ink (y > 330); ʙ's centre (y > 215) is 238,
                  # and 4 scaled by the widths (479/588) is 3 (2026-11-07; the designer's was a's (209, 645))
            0: (241, 645),
        },
        0x029D: {  # ʝ j-crossed-tail
            # 0: (163, 853),  # ymax+clearance−overshoot  # removed 2026-11-07: stage 8 (derived_y) gives j's X plus the shift, at j's Y 834
        },
        0x029F: { # ʟ: above over the stem (98-173), as L's over its stem (2026-11-07; the designer's was a's (209, 645))
            0: (136, 645),
        },

        # Superscript consonants
        0x02B0: {
            0: (155, 914),
            1: (347, 648),
            3: (305, 834),
        },
        0x02B1: {
            0: (151, 913),
            1: (339, 648),
            3: (297, 833),
        },
        0x02B2: {
            0: (73, 914),
            1: (193, 648),
            3: (151, 834),
        },
        0x02B3: {
            0: (128, 805),
            1: (284, 648),
            3: (242, 725),
        },
        0x02B4: {
            0: (120, 805),
            1: (274, 648),
            3: (232, 725),
        },
        0x02B5: {
            0: (143, 805),
            1: (319, 648),
            3: (277, 725),
        },
        0x02B6: {
            0: (142, 805),
            1: (308, 648),
            3: (266, 725),
        },
        0x02B7: {
            0: (229, 805),
            1: (497, 648),
            3: (455, 725),
        },
        0x02B8: {
            0: (171, 805),
            1: (368, 648),
            3: (326, 725),
        },
        0x02E0: {
            0: (155, 858),
            1: (341, 648),
            3: (299, 778),
        },
        0x02E1: {
            0: (79, 914),
            1: (193, 648),
            3: (151, 834),
        },
        0x02E2: {
            # 0: (126, 805),  # removed 2026-10-29: designer's anchor is (128, 805)
            1: (270, 648),
            3: (228, 725),
        },
        0x02E3: {
            # 0: (158, 805),  # removed 2026-10-29: designer's anchor is (158, 805)
            1: (344, 648),
            3: (302, 725),
        },
        0x02E4: {
            0: (131, 914),
            1: (282, 648),
            3: (240, 834),
        },
        0x1D47: {
            0: (139, 914),
            1: (319, 648),
            3: (277, 834),
        },
        0x1D4F: {
            0: (153, 914),
            1: (353, 648),
            3: (311, 834),
        },
        0x1D50: {
            0: (248, 805),
            1: (533, 648),
            3: (491, 725),
        },
        0x1D56: {
            0: (144, 805),
            1: (334, 648),
            3: (292, 725),
        },
        0x1D57: {
            0: (105, 901),
            1: (241, 648),
            3: (199, 821),
        },
        0x1D5A: {
            0: (240, 805),
            1: (525, 648),
            3: (483, 725),
        },
        0x1D5B: {
            # 0: (157, 805),  # removed 2026-10-29: designer's anchor is (158, 805)
            1: (354, 648),
            3: (312, 725),
        },
        0x1D5C: {
            0: (254, 805),
            1: (508, 648),
            3: (466, 725),
        },
        0x1D5D: {
            0: (168, 914),
            1: (335, 648),
            3: (293, 834),
        },
        0x1D5E: {
            0: (175, 812),
            1: (372, 648),
            3: (330, 732),
        },
        0x1D5F: {
            0: (176, 914),
            1: (353, 648),
            3: (311, 834),
        },

#        0x1E1A: {  # Ḛ E tilde below
#            0: (281, 850), # E above anchor
#        },
#        0x1E74: {  # Ṵ U tilde below
#            0: (346, 850), # U above anchor
#        },
#        0x1E75: {  # ṵ u tilde below
#            0: (255, 645), # u above anchor
#        },
        0x1E91: {   # a right half ring
            0: (209, 645),  # a
#            2: (196, -110), # a
            4: (410, 16),   # a
            5: (163, -3),   # a
        },
    },

    "marks": {
        # Tall below marks (2026-11-08): anchor moved up so that the mark rises at most 62 above it,
        # as U+0329 and U+0348; they overlapped descenders at -319 and crowded baseline letters
        # (report, "Mark anchor model", stage 7). x unchanged.
        0x0318: { # left tack below
            2: (-249, -118), # was (-249, -146)
        },
        0x0319: { # right tack below
            2: (-249, -117), # was (-249, -146)
        },
        0x031C: { # left half ring below
            2: (-216, -114), # was (-216, -146)
        },
        0x031F: { # plus sign below
            2: (-249, -115), # was (-249, -145)
        },
        0x0339: { # right half ring below
            2: (-216, -114), # was (-216, -146)
        },
        0x0325: { # ring below
            2: (-218, -94), # was (-218, -116); the precomposed Ḁ ḁ put the ring here (within 2)
        },
        0x034E: { # upwards arrow below
            2: (-227, -90), # was (-227, -110)
        },
    },

    "marks_by_name": {
        # "grave.cap": {
            # 0: (-175, 723), # y implied  # removed 2026-11-08: stage 4 gives (-162, 724), fitted to the
            #                 # precomposed graves (median distance 18 -> 17, median offset +18 -> +6)
        # },
        # "acute.cap": {
            # 0: (-210, 723), # y implied  # removed 2026-10-29: stage 4 gives (-218, 723)
        # },
        # Commented out 2026-10-12: font_patching_capmarks.py now sets these from the
        # precomposed capitals, within 4 units of the curated value (script value at right).
#        "breve.cap": {  # script: (-161, 702)
#            0: (-161, 702), # x mid, y implied
#        },
#        "caron.cap": {  # script: (-184, 677)
#            0: (-184, 677), # x mid, y implied
#        },
#        "dotaccent.cap": {  # script: (146, 736)
#            0: (146, 737), # x mid, y implied
#        },
#        "dieresis.cap": {  # script: (-238, 850)
#            0: (-237, 850), # xmid, y implied
#        },
#        "hookabovecomb.cap": {  # script: (-166, 816)
#            0: (-165, 812) # x mid, y implied
#        },
#        "hungarumlaut.cap": {  # script: (-269, 762)
#            0: (-269, 762), # implied (-226, 747) designer
#        },
#        "uni030F.cap": { # double grave  # script: (-203, 767)
#            0: (-200, 767), # implied. (-220, 745) designer
#        },
#        "breveinvertedcmb.cap": {  # script: (-162, 703)
#            0: (-162,703), # implied
#        },
        # "circumflex.cap" implied matches designer
    },
}
