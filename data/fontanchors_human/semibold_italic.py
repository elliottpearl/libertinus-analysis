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