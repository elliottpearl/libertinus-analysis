# font_context.py

import uharfbuzz as hb
from fontTools.ttLib import TTFont
import json

from .font_helpers import extract_mark_attachment_data
from .config import FONTS_DIR, FONTDATA_DIR


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
        # Fail gracefully if the JSON is malformed
        return {}


class FontContext:
    """
    Container for all per-font data needed by classifiers and helpers.
    Includes:
        - TTFont
        - HBFont
        - cmap
        - markClassByGlyph
        - anchorsByBaseGlyph
        - optional per-font metrics (JSON)
    """

    def __init__(self, ttfont, hb_font, cmap,
                 markClassByGlyph, anchorsByBaseGlyph,
                 metrics=None):
        self.ttfont = ttfont
        self.hb_font = hb_font
        self.cmap = cmap
        self.markClassByGlyph = markClassByGlyph
        self.anchorsByBaseGlyph = anchorsByBaseGlyph
        self.metrics = metrics or {}

    @classmethod
    def from_path(cls, path, lookup_index, font_key=None):
        """
        Load TTFont + HBFont + GPOS anchor data from a font file.
        Optionally loads per-font metrics if font_key is provided.
        """
        ttfont = TTFont(path)
        fontdata = ttfont.reader.file.getvalue()

        hb_face = hb.Face(fontdata)
        hb_font = hb.Font(hb_face)

        markClassByGlyph, anchorsByBaseGlyph, cmap = \
            extract_mark_attachment_data(ttfont, lookup_index)

        metrics = load_font_metrics(font_key) if font_key else {}

        return cls(
            ttfont=ttfont,
            hb_font=hb_font,
            cmap=cmap,
            markClassByGlyph=markClassByGlyph,
            anchorsByBaseGlyph=anchorsByBaseGlyph,
            metrics=metrics,
        )

    # Convenience helpers
    def glyph_name(self, cp):
        return self.cmap.get(cp)

    def class_index_for_mark(self, cp):
        g = self.cmap.get(cp)
        if g is None:
            return None
        return self.markClassByGlyph.get(g)

    def has_anchor(self, base_cp, classIndex):
        base_name = self.cmap.get(base_cp)
        if base_name is None:
            return False
        anchors = self.anchorsByBaseGlyph.get(base_name)
        if anchors is None:
            return False
        return classIndex in anchors

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


# Font configuration
# path is the font file
# lookup_index is the GPOS table index for mark-to-base anchors
# style is a controlled vocabulary font style (italic or boldface), 
# used for LaTeX commands {\itshape } and {\bfseries }
# label is a human-readable label

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
