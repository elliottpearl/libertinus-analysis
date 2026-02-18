"""
ipa_loader.py

Loads IPA/Unicode ground truth data from data/ipa/ipa_unicode.py
and provides helper functions for selecting and grouping items.
"""

from data.ipa import ipa_unicode

# Direct access to authoritative dicts
unicode_groups = ipa_unicode.unicode_groups
MARK_BASE = ipa_unicode.MARK_BASE
mark_class_index = ipa_unicode.mark_class_index


def select_bases(*keys):
    """
    Return a list of base group lists.
    Example:
        select_bases("BASE_LATIN", "BASE_IPA")
    """
    return [getattr(ipa_unicode, k) for k in keys]


def select_marks(*keys):
    """
    Return a list of mark group lists.
    Example:
        select_marks("BASE_ABOVE", "BASE_BELOW")
    """
    return [getattr(ipa_unicode, k) for k in keys]
