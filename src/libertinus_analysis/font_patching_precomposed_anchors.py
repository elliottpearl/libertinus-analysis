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

from .font_patching_anchors import load_human_anchors
from .fontmetrics_helpers import SHIFT_K, SLOPE


ANCHOR_CLASS_NAMES = {
    0: ("above", "base"),
    2: ("below", "base"),
}

# ------------------------------------------------------------
# Unicode-based base resolution
# ------------------------------------------------------------

def get_base_cp_from_unicode(cp):
    """The deepest Unicode decomposition base of cp, as a codepoint."""
    base_cp = cp
    while True:
        parts = unicodedata.decomposition(chr(base_cp)).split()
        if not parts or parts[0].startswith("<"):
            return base_cp
        new_base_cp = int(parts[0], 16)
        if new_base_cp == base_cp:
            return base_cp
        base_cp = new_base_cp


def get_base_from_unicode(cmap, cp):
    """
    Return the *deepest* Unicode decomposition base glyph name.

    Example:
        U+1E14 → "0112 0300" → "0045 0304" → base_cp = 0x0045 → "E"
    """
    base_cp = cp

    while True:
        raw = unicodedata.decomposition(chr(base_cp))
        if not raw:
            break

        parts = raw.split()
        if not parts:
            break

        try:
            new_base_cp = int(parts[0], 16)
        except ValueError:
            break

        # Stop if decomposition does not change the base
        if new_base_cp == base_cp:
            break

        base_cp = new_base_cp

    return cmap.get(base_cp)

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
# Fit of the base letter inside the precomposed glyph
# ------------------------------------------------------------

MIN_FIT = 0.80        # share of the base's ink intervals on the inherited side that must fit
MAX_SCALE_DEV = 0.15  # a fitted scale further than this from 1 is not trusted: shift only
BANDS = {0: (150, 900), 2: (-400, 250)}  # heights compared: the inherited side only

# i and j: their precomposed glyphs are built on the dotless forms
DOTLESS_SOURCE = {0x0069: 0x0131, 0x006A: 0x0237}


def fit_base(ttfont, font_key, derived_glyph, base_glyph, anchor_class, base_xy):
    """
    Return (dx, match, scale): how far the base's anchor moves inside the
    precomposed glyph, from a fit x_derived = scale * x_base + offset of the
    base's ink intervals to the precomposed glyph's, on the inherited side
    only (BANDS), so that a fused cedilla, ogonek or horn on the other side
    does not count. As stem_shift in stage 8: intervals are paired with one of
    about the same width; match is the share of the base's intervals within
    STEM_TOL of the fitted line.
    """
    # imported here: font_patching_derivedanchors imports this module
    from .font_patching_derivedanchors import GRID_STEP, STEM_TOL, _intervals, _segments

    glyphset = ttfont.getGlyphSet()
    slope = SLOPE[font_key]
    k = SHIFT_K.get(font_key, {}).get(str(anchor_class), 0)
    axis = base_xy[0] - base_xy[1] * slope + k
    sd, sb = _segments(glyphset, derived_glyph), _segments(glyphset, base_glyph)
    lo, hi = BANDS[anchor_class]
    pairs, total = [], 0
    for y in range(lo, hi, GRID_STEP):
        y += 0.5
        ib, idv = _intervals(sb, slope, y), _intervals(sd, slope, y)
        total += len(ib)
        for a, b in ib:
            w, c = b - a, (a + b) / 2
            near = [(p + q) / 2 for p, q in idv if abs((q - p) - w) <= 0.2 * w + 4]
            if near:
                pairs.append((c, min(near, key=lambda z: abs(z - c))))
    if len(pairs) < 3 or not total:
        return 0, 0.0, 1.0
    diffs = sorted(d - b for b, d in pairs)
    median = diffs[len(diffs) // 2]
    kept = [(b, d) for b, d in pairs if abs(d - b - median) <= 40]
    mb = sum(b for b, _ in kept) / len(kept)
    md = sum(d for _, d in kept) / len(kept)
    var = sum((b - mb) ** 2 for b, _ in kept)
    scale = sum((b - mb) * (d - md) for b, d in kept) / var if var > 1e-6 else 1.0
    if abs(scale - 1) > MAX_SCALE_DEV:
        scale = 1.0
    offset = md - scale * mb
    good = sum(1 for b, d in kept if abs(scale * b + offset - d) <= STEM_TOL)
    return round(scale * axis + offset - axis), good / total, scale


def load_precomposed_letters():
    """Lists and exclusions from data/precomposed_letters.py."""
    mod = __import__("data.precomposed_letters", fromlist=["PRECOMPOSED_ABOVE"])
    return {
        0: (mod.PRECOMPOSED_ABOVE, mod.EXCLUDED_ABOVE),
        2: (mod.PRECOMPOSED_BELOW, mod.EXCLUDED_BELOW),
    }


# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def patch_precomposed_anchors(ttfont, font_key, anchor_class, lookup_index):
    """
    Give each precomposed letter listed in data/precomposed_letters.py for
    anchor_class (0 above, 2 below) that lacks that anchor its base letter's
    final anchor, moved by the fit of the base inside the precomposed glyph
    (fit_base). The base is the deepest Unicode decomposition base, or ı / ȷ
    for i / j below. Letters excluded for this style, or whose fit is under
    MIN_FIT, are left alone. Existing anchors are never replaced.

    Returns: list of report lines.
    """
    human = load_human_anchors(font_key)
    curated_bases_cp = human.get("bases", {})
    curated_bases_by_name = human.get("bases_by_name", {})

    codepoints, excluded = load_precomposed_letters()[anchor_class]
    style = font_key.removesuffix("_patch")

    report = []
    cmap = ttfont.getBestCmap()

    subtables = find_mark_to_base_subtables(ttfont, lookup_index)
    if not subtables:
        report.append(f"No MarkToBase (LookupType 4) subtables found in lookup {lookup_index}; SKIPPED")
        return report
    sub = subtables[0]

    for cp in codepoints:
        if cp not in cmap:
            report.append(f"U+{cp:04X}: missing from font")
            continue
        glyph_name = cmap[cp]

        if cp in excluded:
            styles, reason = excluded[cp]
            if styles is None or style in styles:
                report.append(f"{glyph_name}: class {anchor_class} excluded ({reason}); SKIPPED")
                continue

        baserec, _ = get_base_record_for_glyph(sub, glyph_name)
        coords = get_anchor_from_baserec(baserec, anchor_class) if baserec is not None else None
        if coords is not None:
            curated = bool(curated_bases_cp.get(cp)) or bool(curated_bases_by_name.get(glyph_name))
            kind = "curated" if curated else "original"
            report.append(f"{glyph_name}: {kind} base anchor class {anchor_class} exists {coords}")
            continue

        base_cp = get_base_cp_from_unicode(cp)
        if anchor_class == 2 and base_cp in DOTLESS_SOURCE:
            base_cp = DOTLESS_SOURCE[base_cp]
        base_name = cmap.get(base_cp)
        if base_name is None:
            report.append(f"{glyph_name}: no Unicode base decomposition; SKIPPED")
            continue

        base_baserec, _ = get_base_record_for_glyph(sub, base_name)
        base_xy = get_anchor_from_baserec(base_baserec, anchor_class) if base_baserec is not None else None
        if base_xy is None:
            report.append(f"{glyph_name}: base '{base_name}' has no anchor class {anchor_class}; SKIPPED")
            continue

        dx, match, scale = fit_base(ttfont, font_key, glyph_name, base_name, anchor_class, base_xy)
        if match < MIN_FIT:
            report.append(f"{glyph_name}: base '{base_name}' fits {match:.0%} on that side, below {MIN_FIT:.0%}; SKIPPED")
            continue

        ax, ay = base_xy[0] + dx, base_xy[1]
        baserec_new, _ = ensure_base_record_for_glyph(sub, glyph_name)
        set_anchor_in_baserec(baserec_new, anchor_class, ax, ay)
        fit = f"shift {dx:+d}" + (f", scale {scale:.3f}" if abs(scale - 1) > 1e-3 else "")
        report.append(f"{glyph_name}: added inherited anchor class {anchor_class} = ({ax}, {ay}) from '{base_name}' {base_xy}, {fit} (fit {match:.0%})")

    return report
