# font_patching.py — patch a font (revised structure with new steps commented out)
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

# --- Future modules (commented out) ---
# from .font_patching_deleteanchors import delete_bad_anchors
# from .font_patching_normalizeanchors import normalize_anchor_y
# from .font_patching_heuristicanchors import patch_anchors_heuristic


def patch_font(font_key: str) -> None:
    """
    Patch a Libertinus font in multiple stages.

    Current behavior is identical to the original pipeline.
    New steps are included but commented out so that this file
    can be used immediately without requiring new modules.
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

    # ------------------------------------------------------------
    # 1. Delete bad anchors (NEW — currently disabled)
    # ------------------------------------------------------------
    # delete_bad_anchors(ttfont, font_key)

    # ------------------------------------------------------------
    # 2. Add glyphs (spacing base glyph, etc.)
    #    Refresh cmap is conceptually part of this step.
    # ------------------------------------------------------------
    add_custom_glyphs(ttfont, font_key)

    # Refresh cmap after glyph additions
    ctx.cmap = ttfont.getBestCmap()
    cmap = ctx.cmap
    cmap_reverse = {g: u for u, g in cmap.items()}

    # ------------------------------------------------------------
    # 3. Patch anchors using human-curated data
    # ------------------------------------------------------------
    patch_anchors_human(
        ttfont=ttfont,
        font_key=font_key,
        lookup_index=lookup_index,
        cmap=cmap,
        cmap_reverse=cmap_reverse,
    )

    # ------------------------------------------------------------
    # 4. Normalize designer-set anchor Y values (NEW — disabled)
    # ------------------------------------------------------------
    # normalize_anchor_y(ttfont, font_key, lookup_index)

    # ------------------------------------------------------------
    # 5. Patch heuristic anchors (NEW — disabled)
    # ------------------------------------------------------------
    # patch_anchors_heuristic(
    #     ttfont=ttfont,
    #     font_key=font_key,
    #     cmap=cmap,
    #     cmap_reverse=cmap_reverse,
    #     lookup_index=lookup_index,
    # )

    # ------------------------------------------------------------
    # 6. Patch precomposed anchors (existing)
    # ------------------------------------------------------------
    report_above = patch_precomposed_anchors(ttfont, font_key, 0, "BASE_ABOVE", lookup_index)
    report_below = patch_precomposed_anchors(ttfont, font_key, 2, "BASE_BELOW", lookup_index)

    for line in report_above + report_below:
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 7. Patch GSUB using human-curated .fea file
    # ------------------------------------------------------------
    patch_gsub_ccmp(ttfont, font_key)

    # ------------------------------------------------------------
    # 8. Save patched font
    # ------------------------------------------------------------
    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")
