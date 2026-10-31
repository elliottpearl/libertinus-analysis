# font_patching.py — patch a font
"""
Top-level orchestration for patching Libertinus fonts.

This module is designed to be called from a wrapper script such as:
    from libertinus_analysis.font_patching import patch_font
    patch_font("regular")

Stages, in order (each is its own module):

     1. clean up the lookup:
        merge semibold top_punkt      font_patching_mergeclasses
        delete bad anchors            font_patching_deleteanchors
     2. add glyphs (spacing base, CGJ) font_patching_addglyphs
     3. add missing marks             font_patching_addmarks
     4. capital-mark anchors          font_patching_capmarks
     5. normalize designer anchor y   font_patching_normalizeanchors
     6. heuristic anchors             font_patching_heuristicanchors
     7. human-curated anchors         font_patching_anchors
     8. derived-letter inheritance    font_patching_derivedanchors
     9. precomposed inheritance       font_patching_precomposed_anchors
    10. GSUB ccmp                     font_patching_gsub
    11. sort mark-to-base coverage   font_patching_sortcoverage
    12. save

Glyphs come first, because every later stage may give them anchors. The
scripted anchor stages (4-6) come before the human-curated anchors, so that
a curated anchor always overrules a scripted one. Derived letters (a base
letter plus a bar, hook, tail...) inherit after the curated anchors, so that
they inherit their base letter's final anchor, but never over a curated
anchor of their own. Precomposed glyphs inherit last of the anchor stages, so
that they inherit the final anchors of their bases. GSUB is rebuilt at the end, when every glyph it names exists. The
mark-to-base coverage is sorted last, because every anchor stage appends to it.

Stage 6 gives each Latin and IPA base that still lacks an above or below
anchor the anchor model's candidate (get_anchor_candidate, see
ANCHOR-HEURISTICS.md). It only fills gaps: designer anchors are moved only by
stage 5, and curated anchors (stage 7) overrule its candidates.
"""

from .font_context import FontContext, FONTS
from .font_patching_addglyphs import add_custom_glyphs
from .font_patching_addmarks import add_cap_dot, add_missing_marks
from .font_patching_anchors import patch_anchors_human
from .font_patching_capmarks import patch_cap_mark_anchors
from .font_patching_deleteanchors import delete_bad_anchors
from .font_patching_derivedanchors import patch_derived_anchors
from .font_patching_gsub import patch_gsub_ccmp
from .font_patching_heuristicanchors import patch_anchors_heuristic
from .font_patching_mergeclasses import merge_anchor_classes
from .font_patching_normalizeanchors import normalize_anchor_y
from .font_patching_precomposed_anchors import patch_precomposed_anchors
from .font_patching_sortcoverage import sort_mark_to_base_coverage

# --- Future modules (commented out) ---

# Stage 1 always deletes the anchors marked "delete" in
# data/fontanchors_audit/overrides.py. The audit's own "bad" verdicts are
# also deleted only if DELETE_BAD_ANCHORS is true. It is off because the
# audit's list has not been reviewed: with it on, about 490 anchors are
# deleted and about 150 of them, outside the Latin/IPA scope of stage 6, get
# no replacement; and in semibold italic it deletes the copies of regular's
# anchors that the semibold italic anchor model keeps.
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
    #    Delete bad anchors: the "delete" overrides, and the audit's
    #    bad verdicts if DELETE_BAD_ANCHORS (see above). Stages 6-8
    #    refill them.
    # ------------------------------------------------------------
    for line in merge_anchor_classes(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")

    for glyph_name, classIndex, xy in delete_bad_anchors(
        ttfont, font_key, lookup_index, use_audit=DELETE_BAD_ANCHORS
    ):
        print(f"[{font_key}] {glyph_name}: deleted anchor class {classIndex} {xy}")

    # ------------------------------------------------------------
    # 2. Add glyphs (spacing base glyph, combining grapheme joiner)
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
    # 5. Normalize designer-set anchor Y values
    #    Semibold's capitals move to the capital reference (stage 4
    #    has already moved the .cap mark anchors to match). Anchors
    #    within 5 of a Y reference snap to it; others are reported.
    # ------------------------------------------------------------
    for line in normalize_anchor_y(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 6. Heuristic anchors: the anchor-model candidate for each
    #    Latin/IPA base still lacking an above or below anchor
    # ------------------------------------------------------------
    for line in patch_anchors_heuristic(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")

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
    # 8. Derived letters inherit their base letter's anchor, plus the
    #    outline shift (data/derived_letters.py)
    # ------------------------------------------------------------
    for line in patch_derived_anchors(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 9. Patch precomposed anchors
    # ------------------------------------------------------------
    report_above = patch_precomposed_anchors(ttfont, font_key, 0, "BASE_ABOVE", lookup_index)
    report_below = patch_precomposed_anchors(ttfont, font_key, 2, "BASE_BELOW", lookup_index)

    for line in report_above + report_below:
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 10. Patch GSUB using human-curated .fea file
    #    (GPOS and GDEF are kept across the rebuild)
    # ------------------------------------------------------------
    patch_gsub_ccmp(ttfont, font_key)

    # ------------------------------------------------------------
    # 11. Sort mark-to-base coverage by glyph ID
    #     (the anchor stages append glyphs out of order)
    # ------------------------------------------------------------
    for line in sort_mark_to_base_coverage(ttfont, lookup_index):
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 12. Save patched font
    # ------------------------------------------------------------
    ttfont.save(output_path)
    print(f"Patched font saved to {output_path}")
