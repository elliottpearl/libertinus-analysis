# font_context.py

import uharfbuzz as hb
from fontTools.ttLib import TTFont
import json

from .config import FONTS_DIR, FONTDATA_DIR

# Metrics loader
def load_font_metrics(font_key):
    """
    Load per-font metrics from data/fontdata/<font_key>.json.
    Returns {} if no metrics file exists.
    """
    path = FONTDATA_DIR / f"{font_key}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
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
        style=None,
        label=None,
    ):
        self.ttfont = ttfont
        self.hb_font = hb_font
        self.cmap = cmap
        self.markClassByGlyph = markClassByGlyph
        self.anchorsByBaseGlyph = anchorsByBaseGlyph
        self.metrics = metrics or {}
        self.style = style
        self.label = label

    @classmethod
    def from_path(cls, path, lookup_index, font_key=None, style=None, label=None):
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
            style=style,
            label=label,
        )

    # Convenience helper
    def glyph_name(self, cp):
        return self.cmap.get(cp)

    # Optional metric accessors
    @property
    def base_bbox(self):
        return self.metrics.get("base_bbox")

    @property
    def vertical_ref(self):
        return self.metrics.get("vertical_ref")

    @property
    def superscript_meanline(self):
        return self.metrics.get("superscript_meanline")

    @property
    def extra_anchors(self):
        return self.metrics.get("anchors")



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
        "style": "regular",
        "label": "Regular",
    },
    "regular_patch": {
        "path": FONTS_DIR / "LibertinusSerif-Regular-patch.otf",
        "lookup_index": 4,
        "style": "regular",
        "label": "Regular patched",
    },
    "italic": {
        "path": FONTS_DIR / "LibertinusSerif-Italic.otf",
        "lookup_index": 4,
        "style": "italic",
        "label": "Italic",
    },
    "semibold": {
        "path": FONTS_DIR / "LibertinusSerif-Semibold.otf",
        "lookup_index": 1,
        "style": "bold",
        "label": "Semibold",
    },
    "semibold_italic": {
        "path": FONTS_DIR / "LibertinusSerif-SemiboldItalic.otf",
        "lookup_index": 2,
        "style": "bold_italic",
        "label": "Semibold italic",
    },
}
