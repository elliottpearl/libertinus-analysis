# font_patching_precomposed_anchors.py
"""
Precomposed-anchor inheritance stage of the Libertinus patching pipeline.

Design goals:
    - Work exactly in the same space as font_patching_anchors.py:
        * GPOS MarkToBase (LookupType 4)
        * cmap / cmap_reverse
        * human-curated anchor dicts
    - No GDEF, no glyf, no composite transforms.
    - Use Unicode decomposition to find the semantic base for a precomposed glyph.
    - Distinguish:
        * original anchors (present in font, not in curated dict)
        * curated anchors (present in curated dict)
        * inherited anchors (added by this module)
    - Report-mode + patch-mode in one pass:
        * If anchors already exist → report original/curated, do not change.
        * If anchors missing → inherit from base glyph, add anchors, report.
"""

import unicodedata

from fontTools.ttLib.tables import otTables

from libertinus_analysis import unicode_groups
from .font_patching_anchors import load_human_anchors


ANCHOR_CLASS_NAMES = {
    0: ("above", "base"),
    2: ("below", "base"),
}


# ------------------------------------------------------------
# Unicode-based base resolution
# ------------------------------------------------------------

def get_base_from_unicode(cmap, cp):
    """
    Given a precomposed codepoint cp, return base glyph name using Unicode decomposition.

    For example, U+1EA0 Ạ → decomposition "0041 0323" → base_cp = 0x0041 → "A".

    Returns:
        base_glyph_name (str) or None if no usable decomposition/base.
    """
    ch = chr(cp)
    decomp = unicodedata.decomposition(ch)
    if not decomp:
        return None

    parts = decomp.split()
    if not parts:
        return None

    # First part is the base codepoint
    try:
        base_cp = int(parts[0], 16)
    except ValueError:
        return None

    if base_cp not in cmap:
        return None

    return cmap[base_cp]


# ------------------------------------------------------------
# Helpers for MarkToBase
# ------------------------------------------------------------

def find_mark_to_base_subtables(ttfont, lookup_index):
    """
    Return list of MarkToBase subtables (LookupType 4) for the given lookup_index.
    """
    gpos = ttfont["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]
    return [sub for sub in lookup.SubTable if sub.LookupType == 4]


def get_base_record_for_glyph(sub, glyph_name):
    """
    Return (BaseRecord, index) for glyph_name in this MarkToBase subtable,
    or (None, None) if not present.
    """
    base_cov = sub.BaseCoverage
    base_array = sub.BaseArray

    if glyph_name in base_cov.glyphs:
        idx = base_cov.glyphs.index(glyph_name)
        return base_array.BaseRecord[idx], idx

    return None, None


def ensure_base_record_for_glyph(sub, glyph_name):
    """
    Ensure glyph_name has a BaseRecord in this MarkToBase subtable.
    Return (BaseRecord, index).
    """
    base_cov = sub.BaseCoverage
    base_array = sub.BaseArray
    class_count = sub.ClassCount

    baserec, idx = get_base_record_for_glyph(sub, glyph_name)
    if baserec is not None:
        # Ensure BaseAnchor list matches ClassCount
        while len(baserec.BaseAnchor) < class_count:
            baserec.BaseAnchor.append(None)
        return baserec, idx

    # Create new BaseRecord
    base_cov.glyphs.append(glyph_name)
    baserec = otTables.BaseRecord()
    baserec.BaseAnchor = [None] * class_count
    base_array.BaseRecord.append(baserec)
    idx = len(base_array.BaseRecord) - 1

    return baserec, idx


def get_anchor_from_baserec(baserec, class_index):
    """
    Return (x, y) for BaseAnchor[class_index] in this BaseRecord, or None.
    """
    if class_index >= len(baserec.BaseAnchor):
        return None

    anchor = baserec.BaseAnchor[class_index]
    if anchor is None:
        return None

    return (anchor.XCoordinate, anchor.YCoordinate)


def set_anchor_in_baserec(baserec, class_index, x, y):
    """
    Set BaseAnchor[class_index] in this BaseRecord to (x, y), creating Anchor if needed.
    """
    while len(baserec.BaseAnchor) <= class_index:
        baserec.BaseAnchor.append(None)

    anchor = baserec.BaseAnchor[class_index]
    if anchor is None:
        anchor = otTables.Anchor()
        anchor.Format = 1
        baserec.BaseAnchor[class_index] = anchor

    anchor.XCoordinate = x
    anchor.YCoordinate = y


# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def patch_precomposed_anchors(ttfont, font_key, anchor_class, group_name, lookup_index):
    """
    ttfont: TTFont
    font_key: "regular", etc.
    anchor_class: 0 (above) or 2 (below)
    group_name: key in unicode_groups (e.g. "BASE_ABOVE", "BASE_BELOW")
    lookup_index: same GPOS lookup_index used by patch_anchors_human

    Returns: list of report lines (also printed to stdout).
    """

    # Load curated anchors
    human = load_human_anchors(font_key)
    curated_bases_cp      = human.get("bases", {})
    curated_marks_cp      = human.get("marks", {})
    curated_bases_by_name = human.get("bases_by_name", {})
    curated_marks_by_name = human.get("marks_by_name", {})

    # Load codepoints from unicode_groups
    codepoints = unicode_groups[group_name]["items"]

    report = []
    anchor_name, anchor_kind = ANCHOR_CLASS_NAMES[anchor_class]

    cmap = ttfont.getBestCmap()

    # MarkToBase subtables
    subtables = find_mark_to_base_subtables(ttfont, lookup_index)
    if not subtables:
        line = f"[{font_key}] No MarkToBase (LookupType 4) subtables found in lookup {lookup_index}; SKIPPED"
#        print(line)
        report.append(line)
        return report

    # We assume a single MarkToBase subtable for this font
    sub = subtables[0]
    class_count = sub.ClassCount

    for cp in codepoints:
        if cp not in cmap:
            line = f"U+{cp:04X}: missing from font"
#            print(line)
            report.append(line)
            continue

        glyph_name = cmap[cp]

        # --------------------------------------------------------
        # 1. Check if base anchors already exist for this glyph
        # --------------------------------------------------------
        baserec, _ = get_base_record_for_glyph(sub, glyph_name)
        existing_any = False
        existing_coords = {}

        if baserec is not None:
            for class_index in range(class_count):
                coords = get_anchor_from_baserec(baserec, class_index)
                if coords is not None:
                    existing_any = True
                    existing_coords[class_index] = coords

        if existing_any:
            # Determine if curated
            curated_anchor = False

            # Unicode-keyed curated anchors
            if cp in curated_bases_cp and curated_bases_cp[cp]:
                curated_anchor = True

            # glyph-name-keyed curated anchors
            if glyph_name in curated_bases_by_name and curated_bases_by_name[glyph_name]:
                curated_anchor = True

            if curated_anchor:
                line = (
                    f"{glyph_name}: curated base anchors exist {existing_coords}; "
                    f"should be inherited; consider removing from curated anchors"
                )
            else:
                line = f"{glyph_name}: original base anchors exist {existing_coords}"

#            print(line)
            report.append(line)
            continue

        # --------------------------------------------------------
        # 2. No anchors: try to inherit from semantic base
        # --------------------------------------------------------
        base_name = get_base_from_unicode(cmap, cp)
        if base_name is None:
            line = f"{glyph_name}: no Unicode base decomposition; SKIPPED"
#            print(line)
            report.append(line)
            continue

        base_baserec, _ = get_base_record_for_glyph(sub, base_name)
        if base_baserec is None:
            line = f"{glyph_name}: base '{base_name}' has no base anchors; SKIPPED"
#            print(line)
            report.append(line)
            continue

        # Inherit ONLY the requested anchor_class
        baserec_new, _ = ensure_base_record_for_glyph(sub, glyph_name)

        coords = get_anchor_from_baserec(base_baserec, anchor_class)
        if coords is None:
            line = f"{glyph_name}: base '{base_name}' has no anchor class {anchor_class}; SKIPPED"
            report.append(line)
        else:
            ax, ay = coords
            set_anchor_in_baserec(baserec_new, anchor_class, ax, ay)
            line = f"{glyph_name}: added inherited anchor class {anchor_class} = ({ax}, {ay}) from '{base_name}'"
            report.append(line)

#        print(line)
        report.append(line)

    return report
