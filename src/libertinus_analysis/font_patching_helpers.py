# font_patching_helpers.py

def add_spacing_base_glyph(ttfont, font_key):
    """
    Create the invisible spacing-base glyph U+E100 ("space_en_base"):

    - width = width of 'n' (per style)
    - outline height = x-height (per style)
    - anchors will be added later by curated anchor patcher
    - GDEF class = base
    - CFF-safe CharString
    """

    codepoint = 0xE100
    glyph_name = "space_en_base"

    # Skip if already present
    cmap = ttfont.getBestCmap()
    if codepoint in cmap:
        return

    # Width = width of 'n'
    hmtx = ttfont["hmtx"]
    if "n" not in hmtx.metrics:
        raise ValueError("Font has no 'n' glyph; cannot determine width.")
    n_width, _ = hmtx["n"]
    width = n_width
    # print(f"[diagnostic] width('n') = {n_width} for {font_key}")

    # Style-specific x-height
    XHEIGHTS = {
        "regular": 429,
        "italic": 429,
        "semibold": 433,
        "semibold_italic": 434,
    }
    xh = XHEIGHTS[font_key]

    # Add glyph to glyph order
    glyph_order = ttfont.getGlyphOrder()
    if glyph_name not in glyph_order:
        glyph_order.append(glyph_name)
        ttfont.setGlyphOrder(glyph_order)

    # Add to cmap
    cmap[codepoint] = glyph_name

    # Add to hmtx
    hmtx.metrics[glyph_name] = (width, 0)

    # --- CFF CharString creation ------------------------------------

    cff = ttfont["CFF "].cff
    top = cff.topDictIndex[0]
    cs = top.CharStrings

    # 1. Extend the CharStrings INDEX using the public API
    cs.charStringsIndex.append(None)

    # 2. Valid Type 2 CharString program (OPERANDS FIRST, THEN OPERATOR)
    program = [
        width,          # CFF width operand (required!)
        0, 0, "rmoveto",
        0, xh, "rlineto",
        "endchar",
    ]

    # 3. Clone an existing CharString to get the correct class
    template = cs["n"]

    new_cs = template.__class__(
        globalSubrs=template.globalSubrs,
        private=template.private,
        program=program,
    )
    new_cs.width = width

    # 4. Assign into CharStrings mapping
    cs[glyph_name] = new_cs

    # --- GDEF classification -----------------------------------------

    if "GDEF" in ttfont:
        gdef = ttfont["GDEF"].table
        if gdef.GlyphClassDef is None:
            from fontTools.ttLib.tables.otTables import GlyphClassDef
            gdef.GlyphClassDef = GlyphClassDef()
            gdef.GlyphClassDef.classDefs = {}

        if gdef.GlyphClassDef.classDefs is None:
            gdef.GlyphClassDef.classDefs = {}

        gdef.GlyphClassDef.classDefs[glyph_name] = 1

        