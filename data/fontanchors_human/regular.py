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
"""

anchors = {

    "bases": {
        0x004A: {  # J
            2: (109, -272),
        },
        0x0051: {  # Q
            2: (350, -309),
        },
        0x0062: {  # b
            0: (279, 885),  # apex of bowl
        },
        0x0063: {  # c
            2: (227, -110),
        },
        0x0064: {  # d
            # 0: (385, 885),  # center of stem; ascender aspect. 234 is center left bowl edge + 5 overshooot and right stem right edge
            # 0: (233, 885),  # xmid of left bowl and right stem; ascender aspect.
            0: (234, 885),
            # 2: (222, -110), # xmid of lower bowl extrema; baseline aspect.
            2: (234, -110),
        },
        0x0066: {  # f
            0: (273, 885),  # apex of f
            2: (136, -110),
        },
        0x0068: {  # h
            0: (282, 885),  # center of stems + offset
        },
        0x006A: {  # j
            0: (126, 795),  # shifted by 11 from i
        },
        0x006B: {  # k
            0: (272, 885),  # center of < part + offset
            2: (290, -110),
        },
        0x006D: {  # m
            2: (404, -110),
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
        0x007A: {  # z
            0: (220, 645),
        },
        0x00C0: { # A grave
            2: (308,-110), # A anchor below
        },
        0x00C1: { # Á A acute
            2: (308,-110), # A anchor below
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
        0x00E6: {  # æ ae ligature
            0: (350, 645),
            2: (327, -110),
        },
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
        0x014B: {  # ŋ eng
            2: (265, -319),  # ymin close to ascender height
        },
        0x0153: {  # œ oe ligature
            2: (408, -110),  # center of vertical band
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
        0x0190: {  # Ɛ open E
            0: (248, 850),  # xmid bbox, capital aspect
            2: (248, -110),
        },
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
        0x0276: {  # ɶ OE ligature
            0: (361, 645),  # center of lig band
            2: (361, -110),
        },
        0x0253: {  # ɓ b-hook
            0: (255, 885),  # x at ymax
            2: (235, -110),  # x at ymin
        },
        0x0260: {  # ɠ g-hook
            0: (239, 885),  # matches 0x0261
            2: (226, -319),
        },
        0x0266: {  # ɦ h-hook
            0: (263, 885),  # apex of arm
            2: (262, -110),  # center of counter
        },
        0x026B: {  # ɫ l-tilde
            0: (225, 885),  # center of l
            2: (225, -110),
        },
        0x026C: {  # ɬ l-belt
            0: (225, 885),  # center of l
            2: (225, -110),
        },
        0x026E: {  # ɮ lezh
            0: (135, 885),  # center of l
            2: (275, -319),  # below ezh anchor
        },
        0x0275: {  # ɵ barred-o
            0: (238, 645),  # x from o
            2: (243, -110),
        },
        0x027A: {  # ɺ turned-r-long-leg
            0: (208, 885),  # ascender aspect
        },
        0x027B: {  # ɻ turned-r-hook
            0: (238, 645),  # center of stem
        },
        0x0282: {  # ʂ s-hook
            2: (196, -263),  # ymin -87
        },
        0x0283: {  # ʃ esh
            2: (209, -319),  # descender aspect
        },
        0x028C: {  # ʌ turned-v
            0: (249, 645),  # vertex
            2: (229, -110),  # center of serifs
        },
        0x028E: {  # ʎ turned-y
            0: (209, 885),  # ascender aspect
        },
        0x029D: {  # ʝ j-crossed-tail
            0: (163, 853),  # ymax+clearance−overshoot
        },
        0x023F: {  # ȿ s-swash-tail
            2: (196, -283),  # ymin + meanline anchor
        },
        0x0250: {  # ɐ turned-a
            2: (229, -110),
        },
        0x0251: {  # ɑ alpha
            2: (222, -110),
        },
        0x0252: {  # ɒ turned-alpha
            2: (259, -110),
        },
        0x0263: {  # ɣ gamma
            2: (248, -289),  # ymin -87
        },
        0x026D: {  # ɭ l-hook
            2: (196, -275),  # ymin = -188 → -275
        },
        0x0273: {  # ɳ n-retroflex-hook
            2: (262, -308),  # -319 + 11
        },
        0x1E1A: {  # Ḛ E tilde below
            0: (281, 850), # E above anchor
        },
        0x1E74: {  # Ṵ U tilde below
            0: (346, 850), # U above anchor
        },
        0x1E75: {  # ṵ u tilde below
            0: (255, 645), # u above anchor
        },
        0xE100: { # en space with anchor, en = 542
            0: (271,645),
            2: (271,-110),
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
            0: (126, 805),
            1: (270, 648),
            3: (228, 725),
        },
        0x02E3: {
            0: (158, 805),
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
            0: (157, 805),
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
    },

# Add any combining marks manually
    "marks": {
        
    },
}
