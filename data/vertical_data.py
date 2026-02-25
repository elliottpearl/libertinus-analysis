"""
Veritical font data
font keys: 
    regular, italic, semibold, semibold_italic
vertical_metrics are the horitzontal aspects: 
    ascender, capital, x_height, baseline, descender
anchor_y is the Y coordinate of the anchor at the aspect: 
    above_ascender, above_capital, above_x, below_baseline, below_descender
clearance is the absolute value of the difference between the aspect and anchor_y
"""

VERTICAL_DATA = {
    "vertical_metrics": {
        "ascender": {
            "regular": 698,
            "italic": 688,
            "semibold": 690,
            "semibold_italic": 696,
        },
        "capital": {
            "regular": 645,
            "italic": 645,
            "semibold": 645,
            "semibold_italic": 645,
        },
        "x_height": {
            "regular": 429,
            "italic": 442,
            "semibold": 433,
            "semibold_italic": 447,
        },
        "baseline": {
            "regular": 0,
            "italic": 0,
            "semibold": 0,
            "semibold_italic": 0,
        },
        "descender": {
            "regular": -232,
            "italic": -233,
            "semibold": -238,
            "semibold_italic": -219,
        },
    },

    "anchor_y": {
        "above_ascender": {
            "regular": 885,
            "italic": 890,
            "semibold": 885,
            "semibold_italic": 890,
        },
        "above_capital": {
            "regular": 850,
            "italic": 850,
            "semibold": 850,
            "semibold_italic": 850,
        },
        "above_x": {
            "regular": 645,
            "italic": 645,
            "semibold": 645,
            "semibold_italic": 645,
        },
        "below_baseline": {
            "regular": -110,
            "italic": -110,
            "semibold": -110,
            "semibold_italic": -110,
        },
        "below_descender": {
            "regular": -319,
            "italic": -319,
            "semibold": -319,
            "semibold_italic": -319,
        },
    },

    "clearance": {
        "above_ascender": {
            "regular": 187,
            "italic": 190,
            "semibold": 195,
            "semibold_italic": 194,
        },
        "above_capital": {
            "regular": 205,
            "italic": 205,
            "semibold": 205,
            "semibold_italic": 205,
        },
        "above_x_height": {
            "regular": 216,
            "italic": 216,
            "semibold": 212,
            "semibold_italic": 198,
        },
        "below_baseline": {
            "regular": 110,
            "italic": 110,
            "semibold": 110,
            "semibold_italic": 110,
        },
        "below_descender": {
            "regular": 87,
            "italic": 87,
            "semibold": 81,
            "semibold_italic": 100,
        },
    },
}