# classifier_helpers.py
#
# Minimal helper functions for the combining‑mark classifiers.
# Only glyph‑existence checks, NFC precomposed checks, and
# HarfBuzz shaping remain.

import unicodedata
import uharfbuzz as hb


# ----------------------------------------------------------------------
# Basic glyph existence checks
# ----------------------------------------------------------------------

def missing_glyph(cp, cmap):
    """Return True if the codepoint has no glyph in the cmap."""
    return cmap.get(cp) is None


def missing_precomposed(base_cp, mark_cp, cmap):
    """
    Return True if the NFC(base+mark) character exists in Unicode but
    is missing from the font's cmap.
    """
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)
    if len(nfc) == 1:
        composed_cp = ord(nfc)
        return cmap.get(composed_cp) is None
    return False


# ----------------------------------------------------------------------
# HarfBuzz shaping
# ----------------------------------------------------------------------

def shape_pair(hb_font, base_cp, mark_cp):
    """
    Shape base+mark and return (infos, positions), where infos is the
    list of glyph infos and positions is the list of glyph positions.
    """
    buf = hb.Buffer()
    buf.add_str(chr(base_cp) + chr(mark_cp))
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)
    infos = buf.glyph_infos
    positions = buf.glyph_positions
    return infos, positions
    