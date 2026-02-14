# classifiers.py

import unicodedata

from .classifier_helpers import (
    missing_glyph,
    missing_precomposed,
    shape_pair,
    detect_substitution,
    has_anchor,
)

from .ipa_loader import ipa_diacritic_bases


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

    # 4. GSUB substitution (dotless i/j, etc.)
    if detect_substitution(base_cp, mark_cp, infos, cmap, fontctx.ttfont):
        return "substituted", infos, positions

    # 5. True precomposed Unicode character
    if len(infos) == 1:
        seq = chr(base_cp) + chr(mark_cp)
        nfc = unicodedata.normalize("NFC", seq)
        if len(nfc) == 1 and ord(nfc) in cmap:
            return "precomposed", infos, positions

    # 6. Anchored vs fallback using curated classIndex
    if classIndex is not None and has_anchor(
        base_cp, classIndex, fontctx.anchorsByBaseGlyph, cmap
    ):
        return "anchored", infos, positions
    else:
        return "fallback", infos, positions


def classify_combo_sanity(base_cp, mark_cp, classIndex, fontctx):
    """
    Sanity classifier for IPA-relevant combining marks.

    Returns:
        (kind, flags, infos, positions)

    kind ∈ {
        "unsupported",
        "precomposed",
        "anchored",
        "fallback",
    }
    """

    cmap = fontctx.cmap

    flags = {
        "missing_base": False,
        "missing_mark": False,
        "missing_precomposed": False,
        "gsub_substitution": False,
    }

    # IPA semantic support
    supported_bases = ipa_diacritic_bases.get(mark_cp, [])
    supported = base_cp in supported_bases

    # Missing glyphs
    if missing_glyph(base_cp, cmap):
        flags["missing_base"] = True
    if missing_glyph(mark_cp, cmap):
        flags["missing_mark"] = True

    if flags["missing_base"] or flags["missing_mark"]:
        infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)
        return "unsupported", flags, infos, positions

    # Shape
    infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)

    # GSUB substitution
    if detect_substitution(base_cp, mark_cp, infos, cmap, fontctx.ttfont):
        flags["gsub_substitution"] = True

    # Precomposed
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)
    if len(nfc) == 1:
        composed_cp = ord(nfc)
        if cmap.get(composed_cp) is not None:
            kind = "precomposed" if supported else "unsupported"
            return kind, flags, infos, positions
        else:
            flags["missing_precomposed"] = True

    # Anchored vs fallback
    if classIndex is not None and has_anchor(
        base_cp, classIndex, fontctx.anchorsByBaseGlyph, cmap
    ):
        kind = "anchored"
    else:
        kind = "fallback"

    if not supported:
        kind = "unsupported"

    return kind, flags, infos, positions

__all__ = [
    "classify_combo",
    "classify_combo_sanity",
]
