# Anchor data
# 0 above. 2 below

anchors = {
    "bases": {
        0x04F: { # O
            2: (310, -110) # normalize by
        },
        0x0059: { # Y
             2: (270, -110) # Y normalize
        },
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
        0x19F: { # O middle tilde
            0: (515, 850), # O
            2: (310, -110) # O
        },
        0x01B1: { # Upsilon
            0: (513, 850), # italic lane
            2: (310, -110), # italic lane
        },
        0x01B2: { # V hook
            0: (506, 850), # italic lane
            2: (302, -110) # italic lane
        },
        0x01B3: { # Y hook
            0: (511, 850), # italic lane of stem
            2: (342, -110) # italic lane of stem
        },
        0x01B5: { # Z stroke
            0: (489, 850), # italic lane
            2: (286, -110) # italic lane
        },
        0xE100: { # en space with anchor, width = 320
            0: (160,645),
            2: (160,-110),
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
        "breve.cap": {
            0: (-10, 703), # x mid, y implied
        },
        "caron.cap": {
            0: (-50, 677), # x vertex, y implied. text x = -36?
        },
#        "dotaccent.cap" no such italic glyph
        "dieresis.cap": {
            0: (-75, 857), # xmid, y implied. test x
        },
        "hookabovecomb.cap": {
            0: (-27, 811) # x apex, y implied
        },
        "hungarumlaut.cap": {
            0: (-109, 762), # implied. test other x?
        },
        "uni030F.cap": { # double grave
            0: (-47, 766), # implied. test other x?
        },
        "breveinvertedcmb.cap": {
            0: (-23, 703), # implied
        },
        "circumflex.cap": {
            0: (16, 680), # implied
        },
    },    
}
