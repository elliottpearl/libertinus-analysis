"""
libertinus_analysis package

This package provides tools for analyzing mark-to-base attachment
behavior in Libertinus fonts and generating LaTeX diagnostic reports.
"""

from .font_context import FontContext, FONTS
from .combo_matrix import ComboMatrix
from .ipa_loader import ipa_diacritic_bases, unicode_groups, MARK_CLASS_INDEX

__all__ = [
    "FontContext",
    "FONTS",
    "ComboMatrix",
    "ipa_diacritic_bases",
    "unicode_groups",
    "MARK_CLASS_INDEX"
]