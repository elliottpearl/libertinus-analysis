import unicodedata
import uharfbuzz as hb
from fontTools.ttLib import TTFont


# Shape a base+mark pair with HarfBuzz
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


# Extract GPOS MarkToBase anchor data
def extract_mark_attachment_data(font, lookup_index):
    """
    Extract mark-to-base anchor data from a GPOS lookup.

    Returns:
        markClassByGlyph:   mark glyphName → classIndex
        anchorsByBaseGlyph: base glyphName → {classIndex: anchor}
        cmap:               Unicode → glyphName
    """
    cmap = font.getBestCmap()
    gpos = font["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    markClassByGlyph = {}
    anchorsByBaseGlyph = {}

    for sub in lookup.SubTable:
        if sub.LookupType != 4:  # MarkToBase
            continue

        # MARK ARRAY
        mark_records = sub.MarkArray.MarkRecord
        mark_glyphs = sub.MarkCoverage.glyphs

        for i, glyph in enumerate(mark_glyphs):
            markClassByGlyph[glyph] = mark_records[i].Class

        # BASE ARRAY
        base_records = sub.BaseArray.BaseRecord
        base_glyphs = sub.BaseCoverage.glyphs

        for i, glyph in enumerate(base_glyphs):
            baserec = base_records[i]
            anchors = {}
            for classIndex, anchor in enumerate(baserec.BaseAnchor):
                if anchor is not None:
                    anchors[classIndex] = anchor
            anchorsByBaseGlyph[glyph] = anchors

    return markClassByGlyph, anchorsByBaseGlyph, cmap


# Classification helpers

def missing_glyph(cp, cmap):
    """
    Return True if cp is not mapped in cmap.
    """
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


def detect_substitution(base_cp, mark_cp, infos, cmap, font):
    """
    Detect whether GSUB substituted either base or mark glyph.
    """
    base_name = cmap.get(base_cp)
    mark_name = cmap.get(mark_cp)

    in_base_gid = font.getGlyphID(base_name) if base_name else None
    in_mark_gid = font.getGlyphID(mark_name) if mark_name else None

    out_base_gid = infos[0].codepoint
    out_mark_gid = infos[1].codepoint if len(infos) > 1 else None

    base_subbed = (in_base_gid is not None and out_base_gid != in_base_gid)
    mark_subbed = (in_mark_gid is not None and out_mark_gid != in_mark_gid)

    return base_subbed or mark_subbed
