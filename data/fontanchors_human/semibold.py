# Anchor data

anchors = {

    "bases": {
        0x0270: { # ɰ turned m with long leg: under the middle stem (2026-11-06); width differs from ɯ, so not derived.
                   # X = middle-stem centre; Y = ɯ's candidate (same arches); no below mark collides except U+0347
            2: (390, -125),
        },
        0x028D: { # ʍ turned w: below centred on the middle foot, not the bbox midpoint
            2: (366, -110),
        },
        0x027C: { # ɼ r with long leg: below on the stem's axis, at the descender reference
            2: (141, -319),
        },
        0x00C6: { # Æ: above between the macron of Ǣ and the acute of Ǽ, which the designer's (510, 850) misses by 55 and 34;
                  # below under the common stroke, not the candidate's midpoint (446)
            0: (555, 850),
            2: (510, -110),
        },
        0x0041: { # A
            2: (330, -110), # centre between the serif feet, 109 and 551.5; bbox midpoint 350 is too far right
        },
        0x0192: { # f with hook (florin); no designer anchors, stem ~7 deg
            0: (336, 885),  # apex, as regular f: 10 left of the apex centre (346)
            2: (104, -255), # Y: candidate (tail ends at -170); 37% from foot (73) to stem (156), as italic f
        },
        0x004F: { # O
            0 : (363, 850), # normalize ay
        },
        0x0053: { # S
            0: (252, 850),  # S, normalize 850
        },
        # 0x0059: { # Y
            # 2: (316, -110) # Z normalize by  # removed 2026-10-29: designer's anchor is (316, -109)
        # },
        0x005A: { # Z
            0: (321, 850), # normalize ay
            2: (308, -110) # normalize by
        },
        0x0061: {  # a
            0: (219, 645),  # x scaled from regular
            2: (205, -110),
        },
        0x0065: {  # e
            0: (249, 645),  # x of ymax
        },
        0x0122: { # Ģ G cedilla/comma
            0: (383, 850), # ymax
        },
        0x015E: { # S with cedilla
            0: (252, 850),  # S
        },
        0x018F: { # Schwa
            0: (331, 850), # centre of the top of the arc (was 353, bbox x mid, 22 right)
            2: (343,-110) # ymin
        },
        # 0x19F: { # O middle tilde
            # 0 : (363, 850), # O  # removed 2026-10-29: inherited from O (stage 8): (363, 802)
        # },
        0x01A9: { # Esh
            0: (283, 850), # xm above
            2: (298, -110) # xm below
        },
        0x01B1: { # Upsilon
            0: (361, 850), # xm above
            2: (333, -110), # ymin
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
            0: (316, 850), # Z
            2: (316, -110) # Z
        },
        # 0x01B7: { # Ezh
            # 0: (321, 850), # xm above  # removed 2026-10-29: candidate (stage 6) gives (316, 850)
        # },
        # 0x028A: { # upsilon
            # 0: (267, 645), # xm  # removed 2026-10-29: designer's anchor is (266, 645)
            # 2: (267, -110), # xm  # removed 2026-10-29: candidate (stage 6) gives (267, -110)
        # },
        0xE100: { # en space with anchor, width = 300
            0: (150,645),
            2: (150,-110),
        },
        0x00A0: { # no-break space, base for a floating mark, width = 250
            0: (125, 645), # x-height aspect; x = W/2
            2: (125, -110),
        },
    },

    "marks": {
        0x0300: { # grave
            0: (-127, 683), # designer (-127, 713); y as acute. x was -156 with no reason (2026-11-06):
                            # -127 is on the mark-axis model, precomposed 37 -> 10 (7 glyphs)
        },
        0x0301: { # acute
            0: (-180, 683), # was (-180, 713)
        },
        0x030A: { # ring above
            0: (-170, 715), # was (-170, 742) after stage 1; height of the ring in ů
        },
        0x030D: { # vertical line above
            0: (-137, 688), # was (-137, 719), as U+030E; same as the other styles
        },
        # Mark-axis snap (2026-11-06): X = C + d, d = regular's offset from the axis;
        # checked against the precomposed glyphs (median distance, before -> after).
        0x0311: { # inverted breve
            0: (-217, 645), # was (-205, 645); precomposed 11 -> 4 (5 glyphs)
        },
        0x0330: { # tilde below
            2: (-200, -70), # was (-213, -70); precomposed 13 -> 4 (6 glyphs)
        },
    },
}
