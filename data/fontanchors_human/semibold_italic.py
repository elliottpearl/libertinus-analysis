# Anchor data
# 0 above. 2 below

anchors = {
    "bases": {
        0x018F: { # Schwa
            0: (335, 850), # mark axis through the centre of the top of the arc, - K (candidate 369 was 34 right)
        },
        0x0259: { # schwa
            2: (186, -110), # mark axis through the centre of the bottom of the bowl, - K (candidate 227 was 41 right)
        },
        0x0192: { # f with hook (florin); no designer anchors, stem ~19 deg
            0: (386, 890),  # mark axis 10 left of the apex centre (507) at the apex, - K (150)
            2: (60, -255),  # Y: candidate (tail ends at -170); mark axis 37% from foot (34) to stem (118), - K (-12)
        },
        0x0059: { # Y
            0: (319, 850), # italic lane - K (150): semibold italic model
            2: (277, -110) # italic lane
        },
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
            0: (232, 850),  # S
        },
        0x0190: { # open-E
            0: (256, 850), # italic lane
        },
        # 0x19F: { # O middle tilde
            # 0: (335, 850), # O  # removed 2026-10-29: inherited from O (stage 8): (335, 850)
            # 2: (350, -110), # O   # removed 2026-10-29: inherited from O (stage 8): (350, -110)
        # },
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
        0x028A: { # upsilon
            0: (219, 645), # italic lane - K (150): semibold italic model
            2: (281, -110), # italic lane
        },
        0xE100: { # en space with anchor, width = 280
            0: (140, 645),
            2: (140, -110),
        },
        0x00A0: { # no-break space, base for a floating mark, width = 274
            0: (118, 645), # x-height aspect; x = W/2 + Y tan 11.5 - K
            2: (127, -110),
        },
    },
    "marks": {
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
    },
}