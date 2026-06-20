# Anchor data

anchors = {

    "bases": {
        0x0053: { # S
            0: (252, 805),  # S, normalize 805
        },
        0x0061: {  # a
            0: (219, 645),  # x scaled from regular
            2: (205, -110),
        },
        0x0065: {  # e
            0: (249, 645),  # x of ymax
        },
        0x015E: { # S with cedilla
            2: (252, 805),  # S
        },
        0x01A9: { # Esh
            0: (283, 850), # xm above
            2: (298, -110) # xm below
        },
        0xE100: { # en space with anchor, width = 300
            0: (150,645),
            2: (150,-110),
        },
    },

    "marks": {
        # (none yet)
    },
}
