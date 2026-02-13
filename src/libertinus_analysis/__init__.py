"""
libertinus_analysis package

This package provides tools for analyzing mark-to-base attachment
behavior in Libertinus fonts and generating LaTeX diagnostic reports.
"""

from .font_context import FontContext, FONTS
from .combo_matrix import ComboMatrix
from .ipa_loader import ipa_base_groups, ipa_mark_groups, ipa_diacritic_bases

__all__ = [
    "FontContext",
    "FONTS",
    "ComboMatrix",
    "ipa_base_groups",
    "ipa_mark_groups",
    "ipa_diacritic_bases",
]