# font_patching_addglyphs.py
"""
Glyph-creation stage of the Libertinus patching pipeline.

Currently adds:
    - U+034F "uni034F", combining grapheme joiner
      (empty, zero-width mark glyph, so that the font covers the character)
"""

from .font_patching_addmarks import _encode, _set_outline


def add_custom_glyphs(ttfont, font_key: str) -> None:
    """
    Add any custom glyphs required before anchor patching.

    Currently:
    - U+034F combining grapheme joiner

    (U+E100 "space_en_base", a PUA spacing base for floating marks, was
    removed on 2026-11-09: a floating mark is NBSP + mark, and U+00A0 has
    anchors in stage 7.)
    """
    add_cgj_glyph(ttfont)


def add_cgj_glyph(ttfont):
    """
    Create the combining grapheme joiner U+034F ("uni034F"), as Gentium Plus
    and Charis SIL define it: no outline, zero advance width, GDEF class mark.

    It changes no positioning: HarfBuzz hides the character with or without a
    glyph. The glyph is there for coverage, so that XeTeX does not report a
    missing character for each \\cgj, and for engines other than HarfBuzz.
    """
    codepoint = 0x034F
    glyph_name = "uni034F"

    # Skip if already present
    if codepoint in ttfont.getBestCmap():
        return

    _set_outline(ttfont, glyph_name, [])
    _encode(ttfont, codepoint, glyph_name)

