# classifier_helpers.py

import unicodedata
import uharfbuzz as hb

# HarfBuzz shaping

def shape_pair(hb_font, base_cp, mark_cp):
    """
    Shape a base+mark pair with HarfBuzz and return (infos, positions).
    """
    text = chr(base_cp) + chr(mark_cp)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)
    return buf.glyph_infos, buf.glyph_positions

# Missing glyphs / missing precomposed

def missing_glyph(cp, cmap):
    """Return True if cp is not mapped in cmap."""
    return cmap.get(cp) is None


def missing_precomposed(base_cp, mark_cp, cmap):
    """
    Return True if NFC(base+mark) is a single codepoint that is not in cmap.
    """
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)
    if len(nfc) == 1:
        composed_cp = ord(nfc)
        return cmap.get(composed_cp) is None
    return False

# GSUB substitution detection

def detect_substitution(base_cp, mark_cp, infos, cmap, ttfont):
    """
    Detect whether GSUB substituted either base or mark glyph.
    """
    base_name = cmap.get(base_cp)
    mark_name = cmap.get(mark_cp)

    in_base_gid = ttfont.getGlyphID(base_name) if base_name else None
    in_mark_gid = ttfont.getGlyphID(mark_name) if mark_name else None

    out_base_gid = infos[0].codepoint
    out_mark_gid = infos[1].codepoint if len(infos) > 1 else None

    base_subbed = (in_base_gid is not None and out_base_gid != in_base_gid)
    mark_subbed = (in_mark_gid is not None and out_mark_gid != in_mark_gid)

    return base_subbed or mark_subbed


# Anchor lookup

def has_anchor(base_cp, classIndex, anchorsByBaseGlyph, cmap):
    """
    Return True if base_cp has an anchor for classIndex in anchorsByBaseGlyph.
    """
    base_name = cmap.get(base_cp)
    if base_name is None:
        return False
    if base_name not in anchorsByBaseGlyph:
        return False
    return classIndex in anchorsByBaseGlyph[base_name]