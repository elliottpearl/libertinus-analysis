# Anchor data
# 0 above. 2 below

anchors = {
    "bases": {
        0x0061: { # a
            2: (251, -110),  # was (174, -108). x-mid of (78,175.5) to (423.5,75.5) on right edge
        },

        0x0066: { # f
            2: (30, -319),  # below anchor
        },
        0xE100: { # en space with anchor, en = 518
            0: (259,645),
            2: (259,-110),
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
}
