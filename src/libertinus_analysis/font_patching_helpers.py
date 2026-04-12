# font_patching_helpers.py

def add_spacing_base_glyph(ttfont, font_key):
    """
    Create the invisible spacing-base glyph U+E100 ("space_en_base"):

    - width = style-specific hardcoded width (YWIDTHS)
    - outline height = x-height (XHEIGHTS)
    - anchors overwritten here
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
    # rsb = 0
    # anchor_x = lsb + (width - lsb - rsb) / 2

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
            from fontTools.ttLib.tables.otTables import GlyphClassDef
            gdef.GlyphClassDef = GlyphClassDef()
            gdef.GlyphClassDef.classDefs = {}

        if gdef.GlyphClassDef.classDefs is None:
            gdef.GlyphClassDef.classDefs = {}

        gdef.GlyphClassDef.classDefs[glyph_name] = 1
