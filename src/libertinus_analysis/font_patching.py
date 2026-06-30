# font_patching.py — patch a font
"""
Top-level orchestration for patching Libertinus fonts.

This module is designed to be called from a wrapper script such as:
    from libertinus_analysis.font_patching import patch_font
    patch_font("regular")
"""

from .font_context import FontContext, FONTS
from .font_patching_addglyphs import add_custom_glyphs
from .font_patching_anchors import patch_anchors_human
from .font_patching_gsub import patch_gsub_ccmp
from .font_patching_precomposed_anchors import patch_precomposed_anchors

def patch_font(font_key: str) -> None:
    """
    Patch a Libertinus font in three stages:
    1. Add glyphs (e.g. spacing base glyph)
    2. (Re)set anchors using human-curated data
    3. Reset GSUB using human-curated .fea
    """

    meta = FONTS[font_key]
    input_path = meta["path"]
    lookup_index = meta["lookup_index"]

    output_path = input_path.with_name(f"{input_path.stem}-patch{input_path.suffix}")

    # Load font context WITHOUT curated anchors
    ctx = FontContext.from_path(
        path=input_path,
        lookup_index=lookup_index,
        font_key=None,      # prevents FontContext from loading curated anchors
        label=meta.get("label", font_key),
    )

    ttfont = ctx.ttfont

    # 1. Add glyphs (spacing base glyph, etc.)
    add_custom_glyphs(ttfont, font_key)

    # 2. Refresh cmap after glyph additions
    ctx.cmap = ttfont.getBestCmap()
    cmap = ctx.cmap
    cmap_reverse = {g: u for u, g in cmap.items()}

    # 3. Patch anchors using human-curated data
    patch_anchors_human(
        ttfont=ttfont,
        font_key=font_key,
        lookup_index=lookup_index,
        cmap=cmap,
        cmap_reverse=cmap_reverse,
    )

    # 4. Patch GSUB using human-curated .fea file
    patch_gsub_ccmp(ttfont, font_key)

    # 5. Patch precomposed anchors (new step)
    report_above = patch_precomposed_anchors(ttfont, font_key, 0, "BASE_ABOVE", lookup_index)
    report_below = patch_precomposed_anchors(ttfont, font_key, 2, "BASE_BELOW", lookup_index)

    for line in report_above + report_below:
        print(f"[{font_key}] {line}")

    # 6. Save patched font
    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")
