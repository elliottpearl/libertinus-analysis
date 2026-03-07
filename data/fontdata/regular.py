# Superscript / modifier letter anchor and metrics data

fontdata = {

    "base_bbox": {
        0x02B0: (10, 364, 301, 739),
        0x02B1: (10, 358, 293, 738),
        0x02B2: (0, 263, 147, 739),
        0x02B3: (18, 365, 238, 637),
        0x02B4: (13, 358, 228, 630),
        0x02B5: (13, 250, 273, 630),
        0x02B6: (22, 364, 262, 638),
        0x02B7: (7, 358, 451, 632),
        0x02B8: (20, 238, 322, 632),
        0x02E0: (15, 358, 295, 683),
        0x02E1: (11, 363, 147, 739),
        0x02E2: (28, 358, 224, 637),
        0x02E3: (18, 364, 298, 633),
        0x02E4: (26, 364, 236, 739),
        0x1D47: (6, 358, 273, 739),
        0x1D4F: (0, 364, 307, 739),
        0x1D50: (10, 365, 487, 637),
        0x1D56: (0, 238, 288, 637),
        0x1D57: (15, 358, 195, 726),
        0x1D58: (14, 358, 308, 632),
        0x1D59: (44, 335, 316, 667),
        0x1D5A: (2, 364, 479, 636),
        0x1D5B: (6, 358, 308, 632),
        0x1D5C: (46, 357, 462, 628),
        0x1D5D: (48, 244, 289, 739),
        0x1D5E: (24, 220, 326, 637),
        0x1D5F: (45, 358, 307, 739),
    },

    # Height of the superscript meanline in Libertinus
    "superscript_meanline": 630,

    # possible values: superscript_meanline, base_yMax, baseline,
    # meanline, xheight, ascender, capheight
    "vertical_ref": {
        0x02B0: "base_yMax",
        0x02B1: "base_yMax",
        0x02B2: "base_yMax",
        0x02B3: "superscript_meanline",
        0x02B4: "superscript_meanline",
        0x02B5: "superscript_meanline",
        0x02B6: "superscript_meanline",
        0x02B7: "superscript_meanline",
        0x02B8: "superscript_meanline",
        0x02E0: "base_yMax",
        0x02E1: "base_yMax",
        0x02E2: "superscript_meanline",
        0x02E3: "superscript_meanline",
        0x02E4: "base_yMax",
        0x1D47: "base_yMax",
        0x1D4F: "base_yMax",
        0x1D50: "superscript_meanline",
        0x1D56: "superscript_meanline",
        0x1D57: "base_yMax",
        0x1D5A: "superscript_meanline",
        0x1D5B: "superscript_meanline",
        0x1D5C: "superscript_meanline",
        0x1D5D: "base_yMax",
        0x1D5E: "base_yMax",
        0x1D5F: "base_yMax",
    },

    # Placeholder for future anchor-ref logic
    "anchor_ref": {
        0: {  # above
        },
        2: {  # below
        },
    },

}
