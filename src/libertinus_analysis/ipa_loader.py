"""
ipa_loader.py

Loads IPA/Unicode ground truth data from data/ipa/ipa_unicode.py
and provides helper functions for selecting and grouping items.
"""

import importlib.util
from pathlib import Path

from libertinus_analysis.config import IPA_DIR

# Load the data module dynamically

DATA_PATH = IPA_DIR / "ipa_unicode.py"

spec = importlib.util.spec_from_file_location("ipa_unicode", DATA_PATH)
ipa_unicode = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ipa_unicode)

# Now all list data is available as attributes of ipa_unicode:
#   ipa_unicode.latin
#   ipa_unicode.mark_above
#   ipa_unicode.ipa_diacritic_bases
#   ipa_unicode.base_anchor_required
#   etc.

# Direct access to authoritative dicts
unicode_groups = ipa_unicode.unicode_groups
ipa_diacritic_bases = ipa_unicode.ipa_diacritic_bases
MARK_CLASS_INDEX = ipa_unicode.MARK_CLASS_INDEX

# Helper functions

def select_bases(*keys):
    """
    Return a list of base group lists.
    Example:
        select_bases("latin", "ipa")
    """
    return [getattr(ipa_unicode, k) for k in keys]


def select_marks(*keys):
    """
    Return a list of mark group lists.
    Example:
        select_marks("above", "below")
    """
    return [getattr(ipa_unicode, k) for k in keys]
