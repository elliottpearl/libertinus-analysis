"""
libertinus_analysis package

This package provides tools for analyzing mark-to-base attachment
behavior in Libertinus fonts and generating LaTeX diagnostic reports.
"""

from .font_context import FontContext, FONTS
from .combo_matrix import ComboMatrix

from .unicode_groups import base_groups, mark_groups
from .ipa_unicode import ipa_diacritics_bases

__all__ = [
    "FontContext",
    "FONTS",
    "ComboMatrix",
    "base_groups",
    "mark_groups",
    "ipa_diacritics_bases",
]