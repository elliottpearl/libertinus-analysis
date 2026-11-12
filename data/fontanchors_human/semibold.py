# Anchor data

anchors = {

    "bases": {
        # Dotted i letters: above as i (2026-11-08); marks that keep the dot (all marks on į ị, U+033F on ɨ) crowded it
        0x0268: { # ɨ
            0: (156, 837), # was (152, 818)
        },
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
        # 0x01B3: { # Y hook
        #     0: (295, 850), # Y
        #     2: (295, -110) # Y
        # },  # removed 2026-11-11: regular's numbers, 78 left of the stem; stage 8 puts it on the stem (stem_axis)
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
        # 0x026D: { # ɭ l with retroflex hook
            # 0: (150, 885),  # above over the stem midline; not inherited (stem match 0%), the candidate (194) was 44 right (2026-11-07)
            #                 # removed 2026-11-08: ɭ is rebuilt from l (stage 2), so stage 8 inherits l's anchors
        # },
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
    },

    "marks": {
        # Above marks moved vertically by Delta y (2026-11-09): the median offset, composed (base + CGJ + mark)
        # minus the designer's precomposed glyphs, on x-height bases, where it is the same (within a few units)
        # on every base. A positive Delta y raises the anchor by that much, so the mark sits that much lower.
        # X unchanged (k within 10 of the mark-axis rule, k = K); in the slanted styles X moves by Delta y tan theta.
        0x0303: { # tilde
            0: (-133, 693), # was (-133, 679); Delta y +14 (ã ẽ ĩ ñ õ ũ ṽ ỹ, all +14)
        },
        0x0304: { # macron
            0: (-205, 613), # was (-205, 625); Delta y -12 (ā ē ī ō ū ȳ ḡ, all -12)
        },
        0x0307: { # dot above
            0: (-169, 678), # was (-169, 699); Delta y -21 (ċ ė ġ ż ȧ ȯ ṁ ṅ …, -20 to -23)
        },

        # Half rings above (2026-11-08): the designer's anchors were class 1 (top_punkt, y 547, 549), raised 96 by
        # stage 1, so they sat 156-158 above the mark's bottom against regular's 126-136, and the marks landed
        # 20-32 low (40-53 above the letter). Now regular's anchor-to-outline offsets (from the outline's centre
        # and bottom), so they land as in regular.
        0x0351: { # left half ring above
            0: (90, 623), # was (100, 643)
        },
        0x0357: { # right half ring above
            0: (82, 613), # was (100, 645)
        },
        # Tall below marks (2026-11-08): anchor moved up so that the mark rises at most 62 above it,
        # as U+0329 and U+0348; they overlapped descenders at -319 and crowded baseline letters
        # (report, "Mark anchor model", stage 7). x unchanged.
        0x0318: { # left tack below
            2: (-249, -118), # was (-224, -148); x centred on the outline, as regular (2026-11-11)
        },
        0x0319: { # right tack below
            2: (-249, -118), # was (-285, -147); x centred on the outline, as regular (2026-11-11)
        },
        # Up and down tack below (2026-11-11): the boxes level, both tops 62 above the anchor
        # (48 below the baseline on x-height letters), as the left and right tacks and the
        # vertical line below; other fonts level the two boxes. X unchanged.
        0x031D: { # up tack below
            2: (-249, -129), # was (-249, -143)
        },
        0x031E: { # down tack below
            2: (-247, -128), # was (-247, -106)
        },
        0x031C: { # left half ring below
            2: (-216, -114), # was (-216, -146)
        },
        0x031F: { # plus sign below
            2: (-249, -116), # was (-249, -146)
        },
        0x0339: { # right half ring below
            2: (-216, -114), # was (-216, -146)
        },
        0x0325: { # ring below
            2: (-218, -96), # was (-218, -116)
        },
        0x034E: { # upwards arrow below
            2: (-227, -90), # was (-227, -110)
        },
        0x0300: { # grave
            0: (-127, 683), # designer (-127, 713); y as acute. x was -156 with no reason (2026-11-06):
                            # -127 is on the mark-axis model, precomposed 37 -> 10 (7 glyphs)
        },
        0x0301: { # acute
            0: (-180, 683), # was (-180, 713)
        },
        # Grave and acute tone marks, added by stage 3 at y 713, 30 below the curated grave and acute;
        # given their anchors, as in regular, where the tone marks share the grave's and acute's (2026-11-11)
        0x0340: { # grave tone mark
            0: (-127, 683), # was (-127, 713)
        },
        0x0341: { # acute tone mark
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
        # Koronis (2026-11-11): the designer's uni0343 is a reference to the horn uni031B, moved
        # up, and had no mark anchor, so it attached to nothing. Placed as regular's and italic's
        # U+0313 (= U+0343): anchor 135 above the outline's bottom and 21.2 left of its ink
        # centroid. The outline is left as it is (to-do: audit referenced commas and horns).
        0x0343: { # Greek koronis
            0: (-92, 539), # was none
        },
    },
    "bases_by_name": {
        "uni027F.desc": {  # ɿ with descender, U+E27F, added in stage 2 (2026-11-09): below under the stem's centre
                            # (stem 172-290) at the descender reference, as q; above is inherited from ɿ in stage 8
            2: (231, -319),
        },
    },
}
