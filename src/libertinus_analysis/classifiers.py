# classifiers.py
#
# Classifiers for combining mark behavior. Produces a semantic category
# (precomposed / anchored / fallback) plus a flags dict describing
# missing glyphs, GSUB expectations, and semantic support. All visual
# decisions are delegated to the renderer.

import unicodedata

from .classifier_helpers import (
    missing_glyph,
    missing_precomposed,
    shape_pair,
    detect_substitution,
    detect_dotless_substitution,
    detect_altcap_substitution,
    mark_has_altcap,
    mark_requires_dot_removal,
    is_capital,
)
from .ipa_loader import MARK_BASE


# ----------------------------------------------------------------------
# Classic classifier
# ----------------------------------------------------------------------

def classify_combo(base_cp, mark_cp, classIndex, fontctx):
    """
    General combining mark classifier.

    Returns:
        (kind, infos, positions)

    kind ∈ {
        "missing",
        "missing_precomposed",
        "precomposed",
        "substituted",
        "anchored",
        "fallback",
    }

    This classifier does not track semantic support or GSUB expectations.
    """

    cmap = fontctx.cmap

    # 1. Missing glyphs
    if missing_glyph(base_cp, cmap) or missing_glyph(mark_cp, cmap):
        return "missing", None, None

    # 2. Missing precomposed
    if missing_precomposed(base_cp, mark_cp, cmap):
        return "missing_precomposed", None, None

    # 3. Shape
    infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)

    # 4. GSUB substitution (dotless i/j, precomposed, altcap)
    if detect_substitution(base_cp, mark_cp, infos, cmap, fontctx.ttfont):
        return "substituted", infos, positions

    # 5. True precomposed Unicode character
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)
    if len(nfc) == 1 and ord(nfc) in cmap:
        return "precomposed", infos, positions

    # 6. Anchored vs fallback using curated classIndex
    if classIndex is not None and fontctx.has_anchor(base_cp, classIndex, cmap):
        return "anchored", infos, positions

    return "fallback", infos, positions


# ----------------------------------------------------------------------
# Sanity classifier
# ----------------------------------------------------------------------

def classify_combo_sanity(base_cp, mark_cp, classIndex, fontctx):
    """
    Sanity classifier for IPA-relevant combining marks.

    Returns:
        (kind, flags, infos, positions)

    kind ∈ {
        "precomposed",
        "anchored",
        "fallback",
    }

    Unsupported combinations are *not* collapsed into a single kind.
    The renderer uses flags["supported"] to choose supported/unsupported
    coloring for each rendering mode.
    """

    cmap = fontctx.cmap

    flags = {
        "missing_base": False,
        "missing_mark": False,
        "missing_precomposed": False,

        "gsub_prec_expected": False,
        "gsub_prec_occurred": False,

        "gsub_dotless_expected": False,
        "gsub_dotless_occurred": False,

        "gsub_altcap_expected": False,
        "gsub_altcap_occurred": False,

        "supported": False,
    }

    # ------------------------------------------------------------------
    # Semantic support
    # ------------------------------------------------------------------

    supported_bases = MARK_BASE.get(mark_cp, [])
    flags["supported"] = base_cp in supported_bases

    # ------------------------------------------------------------------
    # Missing glyphs
    # ------------------------------------------------------------------

    if missing_glyph(base_cp, cmap):
        flags["missing_base"] = True
    if missing_glyph(mark_cp, cmap):
        flags["missing_mark"] = True

    if flags["missing_base"] or flags["missing_mark"]:
        infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)
        return "fallback", flags, infos, positions

    # ------------------------------------------------------------------
    # Shape
    # ------------------------------------------------------------------

    infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)

    # ------------------------------------------------------------------
    # GSUB expectations
    # ------------------------------------------------------------------

    # Precomposed GSUB expected if NFC(base+mark) exists in cmap
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)
    if len(nfc) == 1:
        composed_cp = ord(nfc)
        if cmap.get(composed_cp) is not None:
            flags["gsub_prec_expected"] = True

    # Dotless GSUB expected only for i/j + dot-removal marks
    if chr(base_cp) in ("i", "j") and mark_requires_dot_removal(mark_cp):
        flags["gsub_dotless_expected"] = True

    # Alt-cap GSUB expected for capital bases with alt-cap marks
    if is_capital(base_cp) and mark_has_altcap(mark_cp):
        flags["gsub_altcap_expected"] = True

    # ------------------------------------------------------------------
    # GSUB occurrence detection
    # ------------------------------------------------------------------

    # Precomposed GSUB occurred if shaping produced a single glyph
    if flags["gsub_prec_expected"] and len(infos) == 1:
        flags["gsub_prec_occurred"] = True

    # Dotless GSUB occurred
    if flags["gsub_dotless_expected"] and detect_dotless_substitution(
        base_cp, mark_cp, infos, cmap, fontctx.ttfont
    ):
        flags["gsub_dotless_occurred"] = True

    # Alt-cap GSUB occurred
    if flags["gsub_altcap_expected"] and detect_altcap_substitution(
        base_cp, mark_cp, infos, cmap, fontctx.ttfont
    ):
        flags["gsub_altcap_occurred"] = True

    # Missing precomposed
    if flags["gsub_prec_expected"] and not flags["gsub_prec_occurred"]:
        flags["missing_precomposed"] = True

    # ------------------------------------------------------------------
    # Determine base glyph for anchor lookup
    # ------------------------------------------------------------------

    base_cp_for_anchor = base_cp

    if flags["gsub_dotless_occurred"]:
        shaped_gid = infos[0].codepoint
        base_cp_for_anchor = fontctx.codepoint_from_gid(shaped_gid)

    # ------------------------------------------------------------------
    # Rendering mode
    # ------------------------------------------------------------------

    if flags["gsub_prec_occurred"]:
        kind = "precomposed"
    elif classIndex is not None and fontctx.has_anchor_gid(
        fontctx.gid_from_codepoint(base_cp_for_anchor), classIndex
    ):
        kind = "anchored"
    else:
        kind = "fallback"

    return kind, flags, infos, positions
    