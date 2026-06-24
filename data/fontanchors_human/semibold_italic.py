# Anchor data
# 0 above. 2 below

anchors = {
    "bases": {
        0x0061: { # a
            # 0: (340, 645),  # test was (379,645)
            2: (277, -110),  # x-mid of (78,132) to (475,132) on right edge
        },
        0x0066: { # f
            2: (62, -319),  # below anchor
        },
        0x0122: { # Ģ G cedilla/comma
            0: (383, 850), # G
        },
        0x015E: { # S with cedilla
            0: (232, 805),  # S
        },
        0x19F: { # O middle tilde
            0: (335, 805), # O
            2: (350, -110), # O 
        },
        0x01B1: { # Upsilon
            0: (506, 850), # italic lane
            2: (311, -110), # italic lane
        },
        0xE100: { # en space with anchor, width = 280
            0: (140,645),
            2: (140,-110),
        },
    },
    "marks": {
        0x030B: { # double acute above
            0: (-28, 719),  # -23 = x-mid of bbox, with -5 left offset for acute weight
        },
        0x0330: { # tilde below
            2: (-196, -70), # x-mid of bbox
        },
    },
}