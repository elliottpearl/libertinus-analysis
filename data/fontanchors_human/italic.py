# Anchor data
# 0 above. 2 below

anchors = {
    "bases": {
        0x0192: { # f with hook (florin); no designer anchors, stem ~19 deg
            0: (525, 890),  # mark axis 10 left of the apex centre (494) at the apex
            2: (35, -257),  # Y: candidate (tail ends at -172); mark axis 37% from foot (22) to stem (106), as italic f
        },
        0x0294: { # glottal stop, top 672: above the capline
            0: (376, 867), # 850 + 27 - 10 (bowl overshoot); x = W/2 + Y tan 12
        },
        0x0295: { # pharyngeal, top 683: above the capline
            0: (379, 878), # 850 + 38 - 10 (bowl overshoot); x = W/2 + Y tan 12
        },
        0x04F: { # O
            2: (310, -110) # normalize by
        },
        # 0x0059: { # Y
             # 2: (270, -110) # Y normalize  # removed 2026-10-29: designer's anchor is (270, -109)
        # },
        0x0061: { # a
            2: (251, -110),  # was (174, -108). x-mid of (78,175.5) to (423.5,75.5) on right edge
        },
        0x0066: { # f
            2: (30, -319),  # below anchor
        },
        0x0122: { # Ģ G cedilla/comma
            0: (513, 850), # G
        },
        0x015E: { # S with cedilla
            0: (402, 850),  # S
        },
        0x016B: { # u with macron
            0: (396, 785),  # translated from o with macron
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
        0x0258: { # reversed e
            0: (356, 645), # italic anchor model
        },
        0x0259: { # schwa
            # 0: (356, 645), # italic anchor model  # removed 2026-10-29: candidate (stage 6) gives (356, 645)
            2: (169, -110), # mark axis through the centre of the bottom of the bowl; designer's (212, -114) was 45 right
        },
        0x028A: { # upsilon
            0: (358, 645), # italic lane
            2: (267, -110), # italic lane
        },
        0xE100: { # en space with anchor, width = 320
            0: (160, 645),
            2: (160,-110),
        },
        0x00A0: { # no-break space, base for a floating mark, width = 250
            0: (262, 645), # x-height aspect; x = W/2 + Y tan 12
            2: (102, -110),
        },
    },
    "marks": {
        0x030B: { # double acute above
            0: (-57, 714), # -52 = x-mid of bbox, with -5 offset for acute weght
        },
        0x0330: { # tilde below
            2: (-220, -70), # x-mid of bbox
        },
    },
    "marks_by_name": {
        "grave.cap": {
            0: (-45, 724), # x scaled from regular, y implied (-45, 724). test up?
        },
        "acute.cap": {
            0: (-65, 724), # x scaled from regular. y implied. test x = -73 pull?
        },
        # "breve.cap": {
            # 0: (-10, 703), # x mid, y implied  # removed 2026-10-29: stage 4 gives (-1, 702)
        # },
        "caron.cap": {
            0: (-50, 677), # x vertex, y implied. text x = -36?
        },
#        "dotaccent.cap" no such italic glyph
        # "dieresis.cap": {
            # 0: (-75, 857), # xmid, y implied. test x  # removed 2026-10-29: stage 4 gives (-69, 857)
        # },
        # "hookabovecomb.cap": {
            # 0: (-27, 811) # x apex, y implied  # removed 2026-10-29: stage 4 gives (-19, 816)
        # },
        # "hungarumlaut.cap": {
            # 0: (-109, 762), # implied. test other x?  # removed 2026-10-29: stage 4 gives (-103, 762)
        # },
        "uni030F.cap": { # double grave
            0: (-47, 766), # implied. test other x?
        },
        "breveinvertedcmb.cap": {
            0: (-23, 703), # implied
        },
        # "circumflex.cap": {
            # 0: (16, 680), # implied  # removed 2026-10-29: stage 4 gives (24, 683)
        # },
    },    
}
