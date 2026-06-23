# Anchor data

anchors = {

    "bases": {
        0x004F: { # O
            0 : (363, 805), # normalize ay
        },
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
        0x0122: { # Ģ G cedilla/comma
            0: (383, 805), # ymax
        },
        0x015E: { # S with cedilla
            0: (252, 805),  # S
        },
        0x018F: { # Schwa
            0: (353, 805), # xm
            2: (343,-110) # ymin
        },
        0x19F: { # O middle tilde
            0 : (363, 805), # O
        },
        0x01A9: { # Esh
            0: (283, 805), # xm above
            2: (298, -110) # xm below
        },
        0x01B7: { # Ezh
            0: (321, 805), # xm above
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
