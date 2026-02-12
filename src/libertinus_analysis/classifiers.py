import unicodedata

from .font_helpers import (
    missing_glyph,
    missing_precomposed,
    detect_substitution,
    shape_pair,
)

# IPA data (optional external module)
from .constants import ipa_diacritics_bases

def classify_combo(base_cp, mark_cp, classIndex, fontctx):
    """
    Classifier for general combining mark behavior.

    Returns:
        (kind, infos, positions)

    kind is one of:
        "missing",
        "missing_precomposed",
        "precomposed",
        "substituted",
        "anchored",
        "fallback"
    """

    cmap = fontctx.cmap

    # Missing glyphs
    if missing_glyph(base_cp, cmap) or missing_glyph(mark_cp, cmap):
        return "missing", None, None

    # Missing precomposed form
    if missing_precomposed(base_cp, mark_cp, cmap):
        return "missing_precomposed", None, None

    # Shape with HarfBuzz
    infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)

    # GSUB substitution
    if detect_substitution(base_cp, mark_cp, infos, cmap, fontctx.ttfont):
        return "substituted", infos, positions

    # True precomposed Unicode character
    if len(infos) == 1:
        seq = chr(base_cp) + chr(mark_cp)
        nfc = unicodedata.normalize("NFC", seq)
        if len(nfc) == 1 and ord(nfc) in cmap:
            return "precomposed", infos, positions

    # Anchored vs fallback
    if fontctx.has_anchor(base_cp, classIndex):
        return "anchored", infos, positions
    else:
        return "fallback", infos, positions



def classify_combo_sanity(base_cp, mark_cp, classIndex, fontctx):
    """
    Sanity classifier for IPA-relevant combining marks.

    Returns:
        (kind, flags, infos, positions)

    kind is one of:
        "unsupported",
        "precomposed",
        "anchored",
        "fallback"

    flags is a dict:
        {
            "missing_base": bool,
            "missing_mark": bool,
            "missing_precomposed": bool,
            "gsub_substitution": bool,
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

    # If either glyph is missing, the combination is unsupported
    if flags["missing_base"] or flags["missing_mark"]:
        kind = "unsupported"
        infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)
        return kind, flags, infos, positions

    # Shape with HarfBuzz
    infos, positions = shape_pair(fontctx.hb_font, base_cp, mark_cp)

    # GSUB substitution
    if detect_substitution(base_cp, mark_cp, infos, cmap, fontctx.ttfont):
        flags["gsub_substitution"] = True

    # Precomposed Unicode character
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)

    if len(nfc) == 1:
        composed_cp = ord(nfc)
        if cmap.get(composed_cp) is not None:
            kind = "precomposed"
            if not supported:
                kind = "unsupported"
            return kind, flags, infos, positions
        else:
            flags["missing_precomposed"] = True

    # Anchored vs fallback
    if fontctx.has_anchor(base_cp, classIndex):
        kind = "anchored"
    else:
        kind = "fallback"

    # Semantic override for unsupported IPA combinations
    if not supported:
        kind = "unsupported"

    return kind, flags, infos, positions
