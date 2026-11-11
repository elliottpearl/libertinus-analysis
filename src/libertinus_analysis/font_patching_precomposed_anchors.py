# font_patching_precomposed_anchors.py
"""
Precomposed-letter stage of the Libertinus patching pipeline (stage 9).

Each precomposed Latin letter listed in data/precomposed_letters.py that
lacks an above or below anchor takes its base letter's final anchor (after
stages 1-8), moved by the fit of the base inside the precomposed glyph
(fit_base in font_patching_inherit, shared with stage 8). The base is the
deepest Unicode decomposition base, or ı / ȷ for i / j below.

Unlike stage 8, this stage only fills gaps: an existing anchor (designer or
curated) is reported and never replaced. Letters excluded for the style, or
whose fit is under MIN_FIT, are left to the earlier stages (their weak fits
have curated anchors in stage 7).
"""

import unicodedata

from .font_patching_anchors import load_human_anchors
from .font_patching_inherit import (
    MIN_FIT,
    find_mark_to_base_subtables,
    fit_base,
    get_anchor_from_baserec,
    get_base_record_for_glyph,
    ensure_base_record_for_glyph,
    set_anchor_in_baserec,
)

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


# i and j: their precomposed glyphs are built on the dotless forms
DOTLESS_SOURCE = {0x0069: 0x0131, 0x006A: 0x0237}


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
