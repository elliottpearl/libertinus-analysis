#!/usr/bin/env python3

from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib.tables import otTables

from libertinus_analysis.constants import (
    superscript_consonant,
    base_bbox,
    vertical_ref,
    superscript_meanline,
    anchors,
)

# Bounding box geometry

def get_bbox(glyph_set, glyph_name):
    """Return rounded (xMin, yMin, xMax, yMax) for a glyph."""
    g = glyph_set[glyph_name]
    pen = BoundsPen(glyph_set)
    g.draw(pen)
    bounds = pen.bounds
    if bounds is None:
        return (0, 0, 0, 0)
    xMin, yMin, xMax, yMax = bounds
    return (round(xMin), round(yMin), round(xMax), round(yMax))


def get_bboxes_by_codepoint(font_path):
    """
    Returns {0xXXXX: (xMin, yMin, xMax, yMax)}.
    """
    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    out = {}
    for cp, name in cmap.items():
        out[cp] = get_bbox(glyph_set, name)
    font.close()
    return out


def get_bboxes_with_names(font_path):
    """
    Returns:
        {
            glyph_name: {
                "codepoints": [0xXXXX, ...],
                "bbox": (xMin, yMin, xMax, yMax)
            }
        }
    """
    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()

    # reverse cmap: glyph_name → [codepoints]
    rev = {}
    for cp, name in cmap.items():
        rev.setdefault(name, []).append(cp)

    out = {}
    for name in font.getGlyphOrder():
        out[name] = {
            "codepoints": rev.get(name, []),
            "bbox": get_bbox(glyph_set, name),
        }

    font.close()
    return out


def print_bboxes_list(bboxes):
    """
    bboxes: output of get_bboxes_with_names(font_path)
    Prints lines like:
        ("G",    [0x0047],    (37, -10, 666, 658)),
    sorted by first codepoint; unmapped glyphs last.
    """
    rows = []
    for name, entry in bboxes.items():
        cps = entry["codepoints"]
        bbox = entry["bbox"]
        sort_key = cps[0] if cps else 0xFFFFFFFF
        rows.append((sort_key, name, cps, bbox))
    rows.sort(key=lambda r: r[0])

    for _, name, cps, (xMin, yMin, xMax, yMax) in rows:
        if cps:
            cp_str = ", ".join(f"0x{cp:04X}" for cp in cps)
        else:
            cp_str = ""
        print(f'("{name}",\t[{cp_str}],\t({xMin}, {yMin}, {xMax}, {yMax})),')


# Ancho reference resolution

vertical_ref_y = {}

for cp, ref in vertical_ref.items():
    if ref == "superscript_meanline":
        vertical_ref_y[cp] = superscript_meanline
    elif ref == "base_yMax":
        vertical_ref_y[cp] = base_bbox[cp][3]  # yMax
    else:
        raise ValueError(f"Unsupported vertical_ref value: {ref}")


# Anchor computation (index 0 AND 3)

# anchor1 is for U+0315 (comma above right)
# (markanchor1.x, markanchor1.y) = (-116, 396)
# mark_yMin = 458
# mark_xMin = -142
# clearance1.x = 20
# clearance1.y = 80
#
# baseanchor1.y = meanline + (markanchor1.y - mark_yMin) + clearance1.y
# baseanchor1.y = 630 + (396 - 458) + clearance1.y = 568 + 80 = 648
# baseanchor1_x = base_xMax + (markanchor1.x - mark_xMin) + clearance1_x
# baseanchor1.x = base_xMax + (-116 - (-142)) + 20 = base_xMax + 46
#
# baseanchor3 is for mark U+031A (left angle above)
# (mark_x, mark_y) is mark's anchor.
# mark_yMin and mark_xMin are from mark's bbox.
# clearance_x and clearance_y are your chosen clearances.
# baseanchor3.y = vertical_ref_y[cp] + (mark_y - mark_yMin) + clearance_y
#   vertical_ref_y[cp]  is e.g. superscript_meanline or base_yMax.
#   (mark_y - mark_yMin) is mark’s internal anchor offset.
# baseanchor3.x = base_bbox[cp][2] + (mark_x - mark_xMin) + clearance_x
#   base_bbox[cp][2] is base_xMax.
#   (mark_x - mark_xMin) is mark’s internal anchor offset.

def compute_baseanchor3(clearance_x=-20, clearance_y=70):
    """
    Compute anchor class 3 (left angle above) for superscript consonants
    and print a block suitable for anchors[3].
    """
    # Mark U+031A (left angle above)
    mark_x = 18
    mark_y = 580
    mark_xMin = -6
    mark_yMin = 555

    out = {}
    for cp in superscript_consonant:
        xMin, yMin, xMax, yMax = base_bbox[cp]
        ref_y = vertical_ref_y[cp]
        ay = ref_y + (mark_y - mark_yMin) + clearance_y
        ax = xMax + (mark_x - mark_xMin) + clearance_x
        out[cp] = (ax, ay)

    print("    3: {")
    for cp in superscript_consonant:
        ax, ay = out[cp]
        print(f"        0x{cp:04X}: ({ax}, {ay}),")
    print("    },")


# anchor0 is for U+0301 (acute), U+0300 (grave), U+0302 (circumflex)
# r, w, y, s, x, b, m, p already have anchor0 at superscript_meanline
# but b needs to be at base_yMax instead.
# Regrardless, we compute all anchor0 values here.
# But we can look old anchor0 values for clearance reference.
# anchor0.x = base_xCenter = (xMin + xMax) / 2
# anchor0.y = vertical_ref_y[cp] + clearance_y
# old anchor0 values for reference:
# 0x02B3: (119, 805)  # r
# 0x02B7: (219, 805)  # w
# 0x02B8: (168, 805)  # y
# 0x02E2: (128, 805)  # s
# 0x02E3: (158, 805)  # x
# 0x1D47: (148, 805)  # b
# 0x1D50: (288, 805)  # m
# 0x1D56: (148, 805)  # p
# We want anchor0.y = 805 for all glyphs whose vertical_ref is superscript_meanline.
# superscript_meanline = 630, so clearance_y = 805 - 630 = 175.

def compute_baseanchor0(clearance_y=175):
    """
    Compute anchor class 0 (acute/grave/circumflex) for superscript consonants
    and print a block suitable for anchors[0].
    """
    out = {}
    for cp in superscript_consonant:
        xMin, yMin, xMax, yMax = base_bbox[cp]
        x_center = (xMin + xMax) // 2
        ref_y = vertical_ref_y[cp]
        y_anchor = ref_y + clearance_y
        out[cp] = (x_center, y_anchor)

    print("    0: {")
    for cp in superscript_consonant:
        ax, ay = out[cp]
        print(f"        0x{cp:04X}: ({ax}, {ay}),")
    print("    },")


# Font patching (GPOS MarkBasePos)

def patch_gpos_font(font_path, out_path):
    """
    Patch a font's GPOS MarkBasePos lookup using the anchors dict
    and save to out_path.
    """
    font = TTFont(font_path)
    gpos = font["GPOS"].table
    cmap = font["cmap"].getcmap(3, 1).cmap  # Unicode → glyph name

    # This assumes the relevant MarkBasePos lookup index is 4.
    lookup = gpos.LookupList.Lookup[4]
    subtable = lookup.SubTable[0]  # MarkBasePos Format 1

    base_cov = subtable.BaseCoverage
    base_array = subtable.BaseArray
    class_count = subtable.ClassCount  # e.g. 7

    for class_id, table in anchors.items():
        for cp, (ax, ay) in table.items():

            # Skip codepoints not in cmap
            if cp not in cmap:
                continue

            gname = cmap[cp]

            # CASE 1: glyph already present in BaseCoverage
            if gname in base_cov.glyphs:
                idx = base_cov.glyphs.index(gname)
                br = base_array.BaseRecord[idx]

            # CASE 2: glyph missing → append new BaseRecord
            else:
                base_cov.glyphs.append(gname)

                br = otTables.BaseRecord()
                br.BaseAnchor = [None] * class_count
                base_array.BaseRecord.append(br)

            # Create anchor object
            anchor = otTables.Anchor()
            anchor.Format = 1
            anchor.XCoordinate = ax
            anchor.YCoordinate = ay
            anchor.AnchorPoint = None

            # Assign anchor to the correct class slot
            br.BaseAnchor[class_id] = anchor

    font.save(out_path)
    font.close()
