# Anchor data

anchors = {

    "bases": {
        0x0041: { # A
            # 2: (330, -110), # centre between the serif feet, 109 and 551.5; bbox midpoint 350 is too far right  # removed 2026-11-07: the candidate (350) is nearer the precomposed glyphs (349)
        },
        0x0042: { # B: no designer anchors. Above at the centroid of the ink above y 330 (2026-11-06),
                  # where regular's designer B, P, R sit (within 4); the bbox midpoint (300) ignores the
                  # narrower upper bowl
            0: (283, 850),
        },
        0x004C: { # L: above on the stem's axis (2026-11-07), where the designer centred the acute of Ĺ (8 left)
            0: (161, 850),
        },
        0x004F: { # O
            0 : (363, 850), # normalize ay
        },
        0x0053: { # S
            # 0: (252, 850),  # S, normalize 850  # removed 2026-11-07: the candidate (238) is nearer the precomposed glyphs (233)
        },
        # 0x0059: { # Y
            # 2: (316, -110) # Z normalize by  # removed 2026-10-29: designer's anchor is (316, -109)
        # },
        0x005A: { # Z
            0: (321, 850), # normalize ay
            # 2: (308, -110) # normalize by  # removed 2026-11-07: within 1 of the candidate
        },
        0x0061: {  # a
            0: (219, 645),  # x scaled from regular
            # 2: (205, -110),  # removed 2026-11-07: the candidate (255) is nearer the precomposed glyphs (232)
        },
        0x0065: {  # e
            0: (249, 645),  # x of ymax
        },
        0x0069: { # i: above on the stem's axis. Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (156, 837),
        },
        0x006A: { # j: above on the stem's axis (the candidate's X is pulled left by the hook). Only marks that skip the ccmp dotless swap use it (U+033F), so it clears the dot: Y is the candidate's
                  # (dot top + clearance; U+033F then sits 55-60 above the dot, 69-74 above o). (2026-11-07)
            0: (162, 837),
        },
        0x006C: { # l: above and below on the stem's midline, as regular (2026-11-07); the designer's (142, 885) was 8 left; (135, -110) was regular's.
                  # ɫ ɬ ɭ ɮ inherit from it
            0: (150, 885),
            2: (150, -110),
        },
        0x0072: { # r: below under the stem, as r in the other styles; the designer's (212, -110) was 60 right of it (2026-11-07)
            2: (152, -110),
        },
        0x00A0: { # no-break space, base for a floating mark, width = 250
            0: (125, 645), # x-height aspect; x = W/2
            2: (125, -110),
        },
        0x00C6: { # Æ: above between the macron of Ǣ and the acute of Ǽ, which the designer's (510, 850) misses by 55 and 34;
                  # below under the common stroke, not the candidate's midpoint (446)
            0: (555, 850),
            2: (510, -110),
        },
        0x0105: { # ą: above as a's (219, 645), plus the shift of ą's upper part (+12: bowl +9..+15) (2026-11-07);
                  # the designer redrew ą, so stage 9's fit is weak (69%), but it is still an a with an ogonek
            0: (231, 645),
        },
        0x0122: { # Ģ G cedilla/comma
            0: (383, 850), # ymax
        },
        0x015E: { # S with cedilla
            0: (252, 850),  # S
        },
        0x018F: { # Schwa
            0: (331, 850), # centre of the top of the arc (was 353, bbox x mid, 22 right)
            # 2: (343,-110) # ymin  # removed 2026-11-07: within 10 of the candidate
        },
        0x0192: { # f with hook (florin); no designer anchors, stem ~7 deg
            0: (336, 885),  # apex, as regular f: 10 left of the apex centre (346)
            2: (104, -255), # Y: candidate (tail ends at -170); 37% from foot (73) to stem (156), as italic f
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
        0x0251: { # ɑ: above at the centre from the bowl's outer edge to the stem's outer edge (2026-11-07), as regular's
                  # designer ɑ (228 on 230) and d; the candidate (276) is pulled right by the stem's foot
            0: (238, 645),
            2: (237, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x0258: { # ɘ reversed e
            2: (212, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x025A: { # ɚ schwa with hook
            2: (199, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x025C: { # ɜ reversed open e
            2: (204, -110),  # below under the lowest point of the bowl, as ə (2026-11-07)
        },
        0x026D: { # ɭ l with retroflex hook
            0: (150, 885),  # above over the stem midline; not inherited (stem match 0%), the candidate (194) was 44 right (2026-11-07)
        },
        0x026E: { # ɮ: below ʒ's below anchor (193) + the shift of the ezh (+90), as regular (2026-11-07)
            2: (283, -319),
        },
        0x0270: { # ɰ turned m with long leg: under the middle stem (2026-11-06); width differs from ɯ, so not derived.
                   # X = middle-stem centre; Y = ɯ's candidate (same arches); no below mark collides except U+0347
            2: (390, -125),
        },
        0x0276: { # ɶ: above over the stroke shared by the o and the E, regular's method (2026-11-07)
            0: (338, 645),
            2: (338, -110),  # below under the stroke shared with the E, as regular (2026-11-07)
        },
        0x0279: { # ɹ: above over the stem top, regular's method (2026-11-07)
            0: (205, 645),
        },
        0x027A: { # ɺ: above over the stem at the ascender reference, as regular (2026-11-07)
            0: (271, 885),
        },
        0x027C: { # ɼ r with long leg: below on the stem's axis, at the descender reference
            2: (141, -319),
        },
        0x027E: { # ɾ: below under the stem, as r (2026-11-07)
            2: (138, -110),
        },
        0x0280: { # ʀ: above as R: R's patched offset from the centre of its upper ink, scaled by the widths, regular's method (2026-11-07)
            0: (241, 645),
        },
        0x0283: { # ʃ: below under the stem, at the descender reference (2026-11-07)
            2: (141, -319),
        },
        # 0x028A: { # upsilon
            # 0: (267, 645), # xm  # removed 2026-10-29: designer's anchor is (266, 645)
            # 2: (267, -110), # xm  # removed 2026-10-29: candidate (stage 6) gives (267, -110)
        # },
        0x028C: { # ʌ: below centre of the gap between the feet, as regular (2026-11-07)
            2: (209, -110),
        },
        0x028D: { # ʍ turned w: below centred on the middle foot, not the bbox midpoint
            # 2: (366, -110),  # removed 2026-11-07: within 10 of the candidate
        },
        0x028E: { # ʎ: above over the apex of the turned V, at the ascender reference, as regular (2026-11-07)
            0: (230, 885),
        },
        0x0293: { # ʓ: above as ʒ's above anchor, at ʒ's Y; the tops match within a few units, regular's method (2026-11-07)
            0: (231, 645),
            2: (236, -415),  # below: ymin -328 minus the descender clearance (87), no overshoot correction (the curl is sharp); X the candidate's (ʒ matches 32-49%) (2026-11-07)
        },
        0x029F: { # ʟ: above over the stem, as L, regular's method (2026-11-07)
            0: (148, 645),
        },
        0xE100: { # en space with anchor, width = 300
            0: (150,645),
            2: (150,-110),
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
