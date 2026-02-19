# font_context.py

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from .config import FONTS_DIR

# Metrics loader
def load_font_metrics(font_key):
    """
    Load per-font metrics from data/fontdata/<font_key>.py.
    Returns {} if no module exists or if loading fails.
    font_key is a key of FONTS: regular, italic, semibold, semibold_italic
    """
    try:
        module = __import__(f"data.fontdata.{font_key}", fromlist=["fontdata"])
        return getattr(module, "fontdata", {})
    except Exception:
        return {}

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


# FontContext class
class FontContext:
    """
    Per-font context for classifiers.

    Includes:
        - TTFont
        - HBFont
        - cmap
        - markClassByGlyph (from curated lookup_index)
        - anchorsByBaseGlyph (from curated lookup_index)
        - optional per-font metrics
    """

    def __init__(
        self,
        ttfont,
        hb_font,
        cmap,
        markClassByGlyph,
        anchorsByBaseGlyph,
        metrics=None,
        label=None,
    ):
        self.ttfont = ttfont
        self.hb_font = hb_font
        self.cmap = cmap
        self.markClassByGlyph = markClassByGlyph
        self.anchorsByBaseGlyph = anchorsByBaseGlyph
        self.metrics = metrics or {}
        self.label = label

    @classmethod
    def from_path(cls, path, lookup_index, font_key=None, label=None):
        """
        Load TTFont + HBFont + cmap + GPOS anchors from a font file.
        lookup_index is the curated index of the MarkToBase lookup.
        """
        ttfont = TTFont(path)
        fontdata = ttfont.reader.file.getvalue()

        hb_face = hb.Face(fontdata)
        hb_font = hb.Font(hb_face)

        cmap = ttfont.getBestCmap()

        # Extract anchors using curated lookup_index
        markClassByGlyph, anchorsByBaseGlyph, _ = extract_mark_attachment_data(
            ttfont, lookup_index
        )

        metrics = load_font_metrics(font_key) if font_key else {}

        return cls(
            ttfont=ttfont,
            hb_font=hb_font,
            cmap=cmap,
            markClassByGlyph=markClassByGlyph,
            anchorsByBaseGlyph=anchorsByBaseGlyph,
            metrics=metrics,
            label=label,
        )

    # Convenience helper
    def glyph_name(self, cp):
        return self.cmap.get(cp)

    # ------------------------------------------------------------------
    # NEW HELPERS FOR DOTLESS SUBSTITUTION HANDLING
    # ------------------------------------------------------------------

    def gid_from_codepoint(self, cp):
        """Return the glyph ID for a Unicode codepoint."""
        return self.cmap.get(cp)

    def codepoint_from_gid(self, gid):
        """Return the Unicode codepoint for a glyph ID (inverse cmap)."""
        inv = {v: k for k, v in self.cmap.items()}
        return inv.get(gid)

    def has_anchor_gid(self, gid, classIndex):
        """
        Return True if the glyph ID has an anchor for the given mark class.
        """
        if gid is None:
            return False
        class_map = self.anchorsByBaseGlyph.get(gid)
        if class_map is None:
            return False
        return classIndex in class_map

    # ------------------------------------------------------------------
    # Original anchor lookup (by codepoint)
    # ------------------------------------------------------------------

    def has_anchor(self, base_cp, classIndex, cmap):
        """
        Return True if the base glyph has an anchor for the given mark class.
        """
        base_gid = cmap.get(base_cp)
        if base_gid is None:
            return False

        class_map = self.anchorsByBaseGlyph.get(base_gid)
        if class_map is None:
            return False

        return classIndex in class_map

"""
Font registry

path is the font file
lookup_index is the GPOS table index for mark-to-base anchors
style is a controlled vocabulary (regular, italic, bold, bold_italic)
label is a human-readable label.
"""

FONTS = {
    "regular": {
        "path": FONTS_DIR / "LibertinusSerif-Regular.otf",
        "lookup_index": 4,
        "label": "Regular",
    },
    "regular_patch": {
        "path": FONTS_DIR / "LibertinusSerif-Regular-patch.otf",
        "lookup_index": 4,
        "label": "Regular patched",
    },
    "italic": {
        "path": FONTS_DIR / "LibertinusSerif-Italic.otf",
        "lookup_index": 4,
        "label": "Italic",
    },
    "semibold": {
        "path": FONTS_DIR / "LibertinusSerif-Semibold.otf",
        "lookup_index": 1,
        "label": "Semibold",
    },
    "semibold_italic": {
        "path": FONTS_DIR / "LibertinusSerif-SemiboldItalic.otf",
        "lookup_index": 2,
        "label": "Semibold italic",
    },
}
