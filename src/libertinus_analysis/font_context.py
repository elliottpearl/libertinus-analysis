# font_context.py

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from .config import FONTS_DIR

# ------------------------------------------------------------
# Extract GPOS MarkToBase anchor data
# ------------------------------------------------------------

def extract_mark_attachment_data(font, lookup_index):
    """
    Extract mark-to-base anchor data from a GPOS lookup.

    Returns:
        anchorsByGlyph: glyphName → {classIndex: anchorRecord}
        cmap:           Unicode → glyphName

    NOTE:
        anchorsByGlyph includes BOTH:
            - mark anchors (from MarkArray)
            - base anchors (from BaseArray)

        This normalizes the anchor model so downstream code does not
        need to distinguish base vs mark glyphs.
    """
    cmap = font.getBestCmap()
    gpos = font["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    anchorsByGlyph = {}

    for sub in lookup.SubTable:
        if sub.LookupType != 4:  # MarkToBase
            continue

        # -------------------------
        # MARK ARRAY (mark anchors)
        # -------------------------
        mark_records = sub.MarkArray.MarkRecord
        mark_glyphs = sub.MarkCoverage.glyphs

        for i, glyph in enumerate(mark_glyphs):
            cls = mark_records[i].Class
            anchor = mark_records[i].MarkAnchor

            if anchor is not None:
                anchorsByGlyph[glyph] = {cls: anchor}
            else:
                anchorsByGlyph[glyph] = {}

        # -------------------------
        # BASE ARRAY (base anchors)
        # -------------------------
        base_records = sub.BaseArray.BaseRecord
        base_glyphs = sub.BaseCoverage.glyphs

        for i, glyph in enumerate(base_glyphs):
            baserec = base_records[i]
            anchors = {}

            for classIndex, anchor in enumerate(baserec.BaseAnchor):
                if anchor is not None:
                    anchors[classIndex] = anchor

            anchorsByGlyph[glyph] = anchors

    return anchorsByGlyph, cmap


# ------------------------------------------------------------
# FontContext class
# ------------------------------------------------------------

class FontContext:
    """
    Per-font context for classifiers and analyzers.

    Includes:
        - TTFont
        - HBFont
        - cmap
        - anchorsByGlyph (anchors for both base and mark glyphs)

    NOTE:
        anchorsByBaseGlyph is preserved as a compatibility alias.
    """

    def __init__(
        self,
        ttfont,
        hb_font,
        cmap,
        anchorsByGlyph,
        label=None,
    ):
        self.ttfont = ttfont
        self.hb_font = hb_font
        self.cmap = cmap

        # Unified GPOS-derived anchors
        self.anchorsByGlyph = anchorsByGlyph

        # Backwards compatibility alias
        self.anchorsByBaseGlyph = anchorsByGlyph

        self.label = label

    # ------------------------------------------------------------
    # Construction from a font file
    # ------------------------------------------------------------

    @classmethod
    def from_path(cls, path, lookup_index, font_key=None, label=None):
        """
        Load TTFont + HBFont + cmap + GPOS anchors from a font file.
        """
        ttfont = TTFont(path)
        fontdata = ttfont.reader.file.getvalue()

        hb_face = hb.Face(fontdata)
        hb_font = hb.Font(hb_face)

        cmap = ttfont.getBestCmap()

        anchorsByGlyph, _ = extract_mark_attachment_data(
            ttfont, lookup_index
        )

        return cls(
            ttfont=ttfont,
            hb_font=hb_font,
            cmap=cmap,
            anchorsByGlyph=anchorsByGlyph,
            label=label,
        )

    # ------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------

    def glyph_name(self, cp):
        return self.cmap.get(cp)

    def gid_from_codepoint(self, cp):
        """Return the glyph ID for a Unicode codepoint."""
        return self.cmap.get(cp)

    def codepoint_from_gid(self, gid):
        """Return the Unicode codepoint for a glyph ID (inverse cmap)."""
        inv = {v: k for k, v in self.cmap.items()}
        return inv.get(gid)

    def has_anchor_gid(self, gid, classIndex):
        """
        Return True if the glyph ID has a GPOS anchor for the given mark class.
        """
        if gid is None:
            return False
        class_map = self.anchorsByGlyph.get(gid)
        if class_map is None:
            return False
        return classIndex in class_map

    def has_anchor(self, base_cp, classIndex, cmap):
        """
        Return True if the base glyph has a GPOS anchor for the given mark class.
        """
        base_gid = cmap.get(base_cp)
        if base_gid is None:
            return False

        class_map = self.anchorsByGlyph.get(base_gid)
        if class_map is None:
            return False

        return classIndex in class_map


# ------------------------------------------------------------
# Font registry
# ------------------------------------------------------------

FONTS = {
    "regular": {
        "path": FONTS_DIR / "LibertinusSerif-Regular.otf",
        "lookup_index": 4,
        "label": "Regular",
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
    "regular_patch": {
        "path": FONTS_DIR / "LibertinusSerif-Regular-patch.otf",
        "lookup_index": 4,
        "label": "Regular patched",
    },
    "italic_patch": {
        "path": FONTS_DIR / "LibertinusSerif-Italic-patch.otf",
        "lookup_index": 4,
        "label": "Italic patched",
    },
    "semibold_patch": {
        "path": FONTS_DIR / "LibertinusSerif-Semibold-patch.otf",
        "lookup_index": 1,
        "label": "Semibold patched",
    },
    "semibold_italic_patch": {
        "path": FONTS_DIR / "LibertinusSerif-SemiboldItalic-patch.otf",
        "lookup_index": 2,
        "label": "Semibold italic patched",
    },
}
