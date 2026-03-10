# classifiers.py
#
# Classifiers for combining mark behavior. Each classifier returns a
# semantic category (precomposed / anchored / fallback) plus a flags
# dict describing missing glyphs and basic support. Rendering decisions
# are handled by the renderer.

import unicodedata

from .classifier_helpers import (
    missing_glyph,
    missing_precomposed,
    shape_pair,
)
from .ipa_loader import MARK_BASE


# ----------------------------------------------------------------------
# Sanity classifier
# ----------------------------------------------------------------------

def classify_combo_sanity(base_cp, mark_cp, classIndex, fontctx):
    """
    Sanity classifier for IPA-relevant combining marks.

    Returns:
        (kind, flags, infos, positions)
    """

    cmap = fontctx.cmap

    flags = {
        "missing_base": False,
        "missing_mark": False,
        "missing_precomposed": False,
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

    # If either glyph is missing, shaping still happens but result is fallback
    infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)

    if flags["missing_base"] or flags["missing_mark"]:
        return "fallback", flags, infos, positions

    # ------------------------------------------------------------------
    # Precomposed NFC check
    # ------------------------------------------------------------------

    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)

    if len(nfc) == 1:
        composed_cp = ord(nfc)
        if cmap.get(composed_cp) is not None:
            flags["missing_precomposed"] = False
            return "precomposed", flags, infos, positions
        else:
            flags["missing_precomposed"] = True

    # ------------------------------------------------------------------
    # Anchored vs fallback
    # ------------------------------------------------------------------

    if classIndex is not None and fontctx.has_anchor(base_cp, classIndex, cmap):
        return "anchored", flags, infos, positions

    return "fallback", flags, infos, positions


# ----------------------------------------------------------------------
# Plain classifier
# ----------------------------------------------------------------------

def classify_combo_plain(base_cp, mark_cp, classIndex, fontctx):
    """
    Plain classifier:
    - Same logic as sanity classifier
    - BUT semantic support is ignored
    - flags["supported"] is always True
    """

    cmap = fontctx.cmap

    flags = {
        "missing_base": False,
        "missing_mark": False,
        "missing_precomposed": False,
        "supported": True,   # forced
    }

    # ------------------------------------------------------------------
    # Missing glyphs
    # ------------------------------------------------------------------

    if missing_glyph(base_cp, cmap):
        flags["missing_base"] = True
    if missing_glyph(mark_cp, cmap):
        flags["missing_mark"] = True

    infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)

    if flags["missing_base"] or flags["missing_mark"]:
        return "fallback", flags, infos, positions

    # ------------------------------------------------------------------
    # Precomposed NFC check
    # ------------------------------------------------------------------

    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)

    if len(nfc) == 1:
        composed_cp = ord(nfc)
        if cmap.get(composed_cp) is not None:
            flags["missing_precomposed"] = False
            return "precomposed", flags, infos, positions
        else:
            flags["missing_precomposed"] = True

    # ------------------------------------------------------------------
    # Anchored vs fallback
    # ------------------------------------------------------------------

    if classIndex is not None and fontctx.has_anchor(base_cp, classIndex, cmap):
        return "anchored", flags, infos, positions

    return "fallback", flags, infos, positions
