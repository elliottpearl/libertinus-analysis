# font_patching_addglyphs.py
"""
Glyph-creation stage of the Libertinus patching pipeline.

Currently adds:
    - U+E100 "space_en_base"
      (invisible spacing base glyph used for anchor attachment)
    - U+034F "uni034F", combining grapheme joiner
      (empty, zero-width mark glyph, so that the font covers the character)
"""

from fontTools.ttLib.tables.otTables import GlyphClassDef

from .font_patching_addmarks import _encode, _set_outline


def add_custom_glyphs(ttfont, font_key: str) -> None:
    """
    Add any custom glyphs required before anchor patching.

    Currently:
    - U+E100 "space_en_base" spacing base glyph
    - U+034F combining grapheme joiner
    """
    add_spacing_base_glyph(ttfont, font_key)
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


def add_spacing_base_glyph(ttfont, font_key):
    """
    Create the invisible spacing-base glyph U+E100 ("space_en_base"):

    - width = style-specific hardcoded width (YWIDTHS)
    - outline height = x-height (XHEIGHTS)
    - anchors overwritten later by anchor patcher
    - GDEF class = base
    - preserves legacy CFF behavior including charStringsIndex.append(None)

    Anchors are set later.
    """

    codepoint = 0xE100
    glyph_name = "space_en_base"

    # Skip if already present
    cmap = ttfont.getBestCmap()
    if codepoint in cmap:
        return

    # Load hmtx
    hmtx = ttfont["hmtx"]

    # Style-specific x-height
    XHEIGHTS = {
        "regular": 429,
        "italic": 429,
        "semibold": 433,
        "semibold_italic": 434,
    }
    xh = XHEIGHTS[font_key]

    # Style-specific width
    YWIDTHS = {
        "regular": 280,
        "italic": 320,
        "semibold": 300,
        "semibold_italic": 280,
    }
    width = YWIDTHS[font_key]

    # Add glyph to glyph order
    glyph_order = ttfont.getGlyphOrder()
    if glyph_name not in glyph_order:
        glyph_order.append(glyph_name)
        ttfont.setGlyphOrder(glyph_order)

    # Add to cmap
    cmap[codepoint] = glyph_name

    # Add to hmtx (LSB = 0)
    lsb = 0
    hmtx.metrics[glyph_name] = (width, lsb)

    # --- CFF CharString creation (legacy structure preserved) ---
    cff = ttfont["CFF "].cff
    top = cff.topDictIndex[0]
    cs = top.CharStrings

    # 1. Extend the CharStrings INDEX
    cs.charStringsIndex.append(None)

    # 2. Valid Type 2 CharString program
    program = [
        width,          # width operand
        0, 0, "rmoveto",
        0, xh, "rlineto",
        "endchar",
    ]

    # 3. Clone an existing CharString to get correct class
    template = cs["n"]
    new_cs = template.__class__(
        globalSubrs=template.globalSubrs,
        private=template.private,
        program=program,
    )
    new_cs.width = width

    # 4. Assign into CharStrings mapping
    cs[glyph_name] = new_cs

    # --- GDEF classification (legacy) ---
    if "GDEF" in ttfont:
        gdef = ttfont["GDEF"].table
        if gdef.GlyphClassDef is None:
            gdef.GlyphClassDef = GlyphClassDef()
            gdef.GlyphClassDef.classDefs = {}

        if gdef.GlyphClassDef.classDefs is None:
            gdef.GlyphClassDef.classDefs = {}

        # Class 1 = base glyph
        gdef.GlyphClassDef.classDefs[glyph_name] = 1
