# font_context.py

import uharfbuzz as hb
from fontTools.ttLib import TTFont
import json

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
        return {}


class FontContext:
    """
    Minimal per-font context for classifiers.

    Includes:
        - TTFont
        - HBFont
        - cmap
        - optional per-font metrics (JSON)

    All GPOS-based mark/anchor extraction has been removed.
    """

    def __init__(self, ttfont, hb_font, cmap, metrics=None):
        self.ttfont = ttfont
        self.hb_font = hb_font
        self.cmap = cmap
        self.metrics = metrics or {}

    @classmethod
    def from_path(cls, path, lookup_index=None, font_key=None):
        """
        Load TTFont + HBFont + cmap from a font file.
        lookup_index is ignored (kept only for compatibility).
        """
        ttfont = TTFont(path)
        fontdata = ttfont.reader.file.getvalue()

        hb_face = hb.Face(fontdata)
        hb_font = hb.Font(hb_face)

        cmap = ttfont.getBestCmap()

        metrics = load_font_metrics(font_key) if font_key else {}

        return cls(
            ttfont=ttfont,
            hb_font=hb_font,
            cmap=cmap,
            metrics=metrics,
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
Font configuration

path is the font file
lookup_index is the GPOS table index for mark-to-base anchors
style is a controlled vocabulary (regular, italic, bold, bold_talic) 
of font style, useful for LaTeX commands \\itshape and \\bfseries.
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
