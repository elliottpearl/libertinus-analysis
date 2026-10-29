# font_patching.py — patch a font
"""
Top-level orchestration for patching Libertinus fonts.

This module is designed to be called from a wrapper script such as:
    from libertinus_analysis.font_patching import patch_font
    patch_font("regular")

Stages, in order (each is its own module):

     1. clean up the lookup:
        merge semibold top_punkt      font_patching_mergeclasses
        delete bad anchors            font_patching_deleteanchors   (off)
     2. add the spacing base glyph    font_patching_addglyphs
     3. add missing marks             font_patching_addmarks
     4. capital-mark anchors          font_patching_capmarks
     5. normalize designer anchor y   (planned)
     6. heuristic anchors             (planned)
     7. human-curated anchors         font_patching_anchors
     8. precomposed inheritance       font_patching_precomposed_anchors
     9. GSUB ccmp                     font_patching_gsub
    10. save

Glyphs come first, because every later stage may give them anchors. The
scripted anchor stages (4-6) come before the human-curated anchors, so that
a curated anchor always overrules a scripted one. Precomposed glyphs inherit
last of the anchor stages, so that they inherit the final anchors of their
bases. GSUB is rebuilt at the end, when every glyph it names exists.
"""

from .font_context import FontContext, FONTS
from .font_patching_addglyphs import add_custom_glyphs
from .font_patching_addmarks import add_cap_dot, add_missing_marks
from .font_patching_anchors import patch_anchors_human
from .font_patching_capmarks import patch_cap_mark_anchors
from .font_patching_deleteanchors import delete_bad_anchors
from .font_patching_gsub import patch_gsub_ccmp
from .font_patching_mergeclasses import merge_anchor_classes
from .font_patching_precomposed_anchors import patch_precomposed_anchors

# --- Future modules (commented out) ---
# from .font_patching_normalizeanchors import normalize_anchor_y
# from .font_patching_heuristicanchors import patch_anchors_heuristic

# Stage 1 is implemented but off: until stages 5-6 can refill them, deleted
# anchors with no human-curated replacement fall back to HarfBuzz positioning.
DELETE_BAD_ANCHORS = False

def patch_font(font_key: str) -> None:
    """
    Patch a Libertinus font in multiple stages.
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
    # 1. Clean up the lookup
    #    Merge semibold's second above class (top_punkt) into above,
    #    before any stage copies or sets a mark anchor.
    #    Delete bad anchors (see DELETE_BAD_ANCHORS), listed by
    #    run_anchor_audit.py in data/fontanchors_audit/.
    # ------------------------------------------------------------
    for line in merge_anchor_classes(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")

    if DELETE_BAD_ANCHORS:
        delete_bad_anchors(ttfont, font_key, lookup_index)

    # ------------------------------------------------------------
    # 2. Add glyphs (spacing base glyph)
    # ------------------------------------------------------------
    add_custom_glyphs(ttfont, font_key)

    # ------------------------------------------------------------
    # 3. Add missing marks, with mark anchors
    #    dotaccent.cap in the italic styles; the combining marks
    #    that semibold and semibold italic lack.
    # ------------------------------------------------------------
    for line in add_cap_dot(ttfont, font_key) + add_missing_marks(ttfont, font_key):
        print(f"[{font_key}] {line}")

    # Refresh cmap after glyph additions
    ctx.cmap = ttfont.getBestCmap()
    cmap = ctx.cmap
    cmap_reverse = {g: u for u, g in cmap.items()}

    # ------------------------------------------------------------
    # 4. Capital-mark anchors, from the precomposed capitals
    # ------------------------------------------------------------
    for line in patch_cap_mark_anchors(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 5. Normalize designer-set anchor Y values (planned)
    # ------------------------------------------------------------
    # normalize_anchor_y(ttfont, font_key, lookup_index)

    # ------------------------------------------------------------
    # 6. Patch heuristic anchors (planned)
    # ------------------------------------------------------------
    # patch_anchors_heuristic(
    #     ttfont=ttfont,
    #     font_key=font_key,
    #     cmap=cmap,
    #     cmap_reverse=cmap_reverse,
    #     lookup_index=lookup_index,
    # )

    # ------------------------------------------------------------
    # 7. Patch anchors using human-curated data
    #    Overrules every scripted anchor above.
    # ------------------------------------------------------------
    patch_anchors_human(
        ttfont=ttfont,
        font_key=font_key,
        lookup_index=lookup_index,
        cmap=cmap,
        cmap_reverse=cmap_reverse,
    )

    # ------------------------------------------------------------
    # 8. Patch precomposed anchors
    # ------------------------------------------------------------
    report_above = patch_precomposed_anchors(ttfont, font_key, 0, "BASE_ABOVE", lookup_index)
    report_below = patch_precomposed_anchors(ttfont, font_key, 2, "BASE_BELOW", lookup_index)

    for line in report_above + report_below:
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 9. Patch GSUB using human-curated .fea file
    #    (GPOS and GDEF are kept across the rebuild)
    # ------------------------------------------------------------
    patch_gsub_ccmp(ttfont, font_key)

    # ------------------------------------------------------------
    # 10. Save patched font
    # ------------------------------------------------------------
    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")
