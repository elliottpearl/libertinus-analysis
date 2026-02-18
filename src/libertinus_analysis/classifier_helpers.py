# classifier_helpers.py
#
# Helper functions for the combining mark classifiers. These functions
# provide glyph‑existence checks, HarfBuzz shaping probes, and GSUB
# detection for precomposed, dotless, and alt‑cap substitutions.

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

# ----------------------------------------------------------------------
# GSUB substitution detection
# ----------------------------------------------------------------------

def detect_substitution(base_cp, mark_cp, infos, cmap, ttfont):
    """
    Detect any GSUB substitution by comparing the shaped glyph sequence
    to the expected glyphs for base and mark. This is a coarse check
    used by the classic classifier.
    """
    base_gid = cmap.get(base_cp)
    mark_gid = cmap.get(mark_cp)

    # If shaping produced exactly these two glyphs, no substitution.
    if len(infos) == 2 and infos[0].codepoint == base_gid and infos[1].codepoint == mark_gid:
        return False

    return True

# ----------------------------------------------------------------------
# Dotless substitution detection
# ----------------------------------------------------------------------

# Typographic ground truth: marks that require dot removal on i/j
DOT_REMOVAL_MARKS = {
    0x0300,  # grave
    0x0301,  # acute
    0x0302,  # circumflex
    0x0303,  # tilde
    0x0304,  # macron
    0x0306,  # breve
    0x0307,  # dot above
    0x0308,  # diaeresis
    0x030A,  # ring above
    0x030B,  # double acute
    0x030C,  # caron
}

def mark_requires_dot_removal(mark_cp):
    """Return True if this mark sits directly on the dot of i/j."""
    return mark_cp in DOT_REMOVAL_MARKS


def detect_dotless_substitution(base_cp, mark_cp, infos, cmap, ttfont):
    """
    Detect dotless substitution for i/j by checking the glyph *name*
    of the shaped base. Libertinus uses both 'dotlessj' and 'uni0237'
    depending on the weight, so we accept both.
    """

    if chr(base_cp) not in ("i", "j"):
        return False

    if not infos:
        return False

    shaped_gid = infos[0].codepoint

    try:
        glyph_name = ttfont.getGlyphName(shaped_gid)
    except Exception:
        return False

    # Libertinus uses both Adobe-style and uniXXXX-style names
    DOTLESS_NAMES = {"dotlessi", "dotlessj", "uni0131", "uni0237"}

    return glyph_name in DOTLESS_NAMES

# ----------------------------------------------------------------------
# Alt‑cap substitution detection
# ----------------------------------------------------------------------

def detect_altcap_substitution(base_cp, mark_cp, infos, cmap, ttfont):
    """
    Detect alt‑cap substitution for capital bases with above marks.
    This occurs when the shaped mark glyph differs from the normal
    combining mark glyph.
    """
    if not is_capital(base_cp):
        return False

    if not mark_has_altcap(mark_cp):
        return False

    expected_mark_gid = cmap.get(mark_cp)
    if expected_mark_gid is None:
        return False

    if len(infos) >= 2 and infos[1].codepoint != expected_mark_gid:
        return True

    return False

# ----------------------------------------------------------------------
# Capital detection
# ----------------------------------------------------------------------

def is_capital(cp):
    """Return True if the codepoint is an uppercase letter."""
    return chr(cp).isupper()

# ----------------------------------------------------------------------
# Alt‑cap mark detection
# ----------------------------------------------------------------------

ALT_CAP_MARKS = {
    0x0300,  # grave
    0x0301,  # acute
    0x0302,  # circumflex
    0x0303,  # tilde
    0x0304,  # macron
    0x0306,  # breve
    0x0307,  # dot above
    0x0308,  # diaeresis
    0x030A,  # ring above
    0x030B,  # double acute
    0x030C,  # caron
}

def mark_has_altcap(mark_cp):
    """Return True if the combining mark has a capital‑alternate form."""
    return mark_cp in ALT_CAP_MARKS
