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
     2. add glyphs (CGJ)              font_patching_addglyphs
     3. add missing marks             font_patching_addmarks
     4. capital-mark anchors          font_patching_capmarks
        mark-axis rule                font_patching_markaxis
     5. normalize designer anchor y   font_patching_normalizeanchors
     6. heuristic anchors             font_patching_heuristicanchors
     7. human-curated anchors         font_patching_anchors
        stem-axis rule (7b)           font_patching_stemaxis
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

import json
from pathlib import Path

from .font_context import FontContext, FONTS
from .font_patching_addglyphs import add_custom_glyphs
from .font_patching_addmarks import add_cap_dot, add_cap_tilde, add_missing_marks
from .font_patching_redraw import redraw_glyphs
from .font_patching_anchors import load_human_anchors, patch_anchors_human
from .font_patching_capmarks import patch_cap_mark_anchors
from .font_patching_markaxis import patch_mark_axis
from .font_patching_deleteanchors import delete_bad_anchors
from .font_patching_derivedanchors import patch_derived_anchors
from .font_patching_gsub import patch_gsub_ccmp
from .font_patching_heuristicanchors import patch_anchors_heuristic
from .font_patching_stemaxis import patch_stem_axis
from .font_patching_mergeclasses import merge_anchor_classes
from .font_patching_normalizeanchors import normalize_anchor_y
from .font_patching_precomposed_anchors import patch_precomposed_anchors
from .font_patching_sortcoverage import sort_mark_to_base_coverage

# --- Future modules (commented out) ---

# Stage 1 always deletes the anchors marked "delete" in
# data/fontanchors_audit/overrides.py. The audit's own "bad" verdicts are
# also deleted only if DELETE_BAD_ANCHORS is true. It is off because the
# audit's list is not limited to Latin and IPA, and stage 6 replaces nothing
# outside them. Decisions go in overrides.py as "delete" and "keep".
DELETE_BAD_ANCHORS = False

# The owner of every base anchor in the patched font, per style, written on every
# patch run to data/anchor_provenance/{style}.json as {glyph: {class: owner}}.
# The owner is the last stage that set the anchor:
#   designer     the original font's anchor (after stage 1's merge and deletions), unchanged
#   normalized   the designer's anchor, moved by stage 5 (Y snapped or moved to the capital reference)
#   heuristic    stage 6's candidate
#   curated      stage 7 (data/fontanchors_human/{style}.py), even where it equals the anchor before it
#   stem         stage 7b, the stem-axis rule
#   derived      stage 8, inherited by a derived letter
#   precomposed  stage 9, inherited by a precomposed letter
# The fontmetrics tables of the report read it.
PROVENANCE_DIR = Path(__file__).resolve().parents[2] / "data" / "anchor_provenance"


def _base_anchors(ttfont, lookup_index):
    """{(glyph name, class): (x, y)} of every base anchor in the mark-to-base lookup."""
    found = {}
    lookup = ttfont["GPOS"].table.LookupList.Lookup[lookup_index]
    for sub in lookup.SubTable:
        if sub.LookupType == 9:
            sub = sub.ExtSubTable
        if sub.LookupType != 4:
            continue
        for glyph, record in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
            for cls, anchor in enumerate(record.BaseAnchor):
                if anchor is not None:
                    found[(glyph, cls)] = (anchor.XCoordinate, anchor.YCoordinate)
    return found


def _curated_bases(font_key, cmap):
    """{(glyph name, class)} of the curated base anchors of stage 7."""
    human = load_human_anchors(font_key)
    keys = set()
    for cp, classes in human.get("bases", {}).items():
        if cp in cmap:
            keys.update((cmap[cp], int(c)) for c in classes)
    for glyph, classes in human.get("bases_by_name", {}).items():
        keys.update((glyph, int(c)) for c in classes)
    return keys


def _owners(snapshots, set_by):
    """
    {glyph: {class: owner}} from base-anchor snapshots [(owner, {(glyph, class): xy}), ...],
    the first taken after stage 1 and one after each anchor stage: an anchor is owned by
    the last stage that changed it, or that set it even to the value it had, where
    set_by[stage] lists what the stage set (curated anchors; stage 8's inherited ones).
    """
    owner = {key: snapshots[0][0] for key in snapshots[0][1]}
    for (_, before), (name, after) in zip(snapshots, snapshots[1:]):
        for key, xy in after.items():
            if before.get(key) != xy or key in set_by.get(name, ()):
                owner[key] = name
    result = {}
    for (glyph, cls), name in sorted(owner.items()):
        result.setdefault(glyph, {})[str(cls)] = name
    return result

def patch_font(font_key: str, output_path=None, extra_deletions=frozenset()) -> None:
    """
    Patch a Libertinus font in multiple stages.

    output_path replaces the default *-patch.otf. extra_deletions is a set of
    (glyph name, class) anchors for stage 1 to delete as well; the anchor
    review uses both to build the candidate fonts.
    """

    meta = FONTS[font_key]
    input_path = meta["path"]
    lookup_index = meta["lookup_index"]

    if output_path is None:
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
        ttfont, font_key, lookup_index, use_audit=DELETE_BAD_ANCHORS, extra=extra_deletions
    ):
        print(f"[{font_key}] {glyph_name}: deleted anchor class {classIndex} {xy}")
    snapshots = [("designer", _base_anchors(ttfont, lookup_index))]

    # ------------------------------------------------------------
    # 2. Add glyphs (spacing base glyph, combining grapheme joiner);
    #    outline fixes (semibold ɭ)
    # ------------------------------------------------------------
    add_custom_glyphs(ttfont, font_key)
    for line in redraw_glyphs(ttfont, font_key):
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 3. Add missing marks, with mark anchors
    #    dotaccent.cap in the italic styles; tildecomb.cap; the combining marks
    #    that semibold and semibold italic lack.
    # ------------------------------------------------------------
    for line in (add_cap_dot(ttfont, font_key) + add_cap_tilde(ttfont, font_key)
                 + add_missing_marks(ttfont, font_key)):
        print(f"[{font_key}] {line}")

    # Refresh cmap after glyph additions
    ctx.cmap = ttfont.getBestCmap()
    cmap = ctx.cmap
    cmap_reverse = {g: u for u, g in cmap.items()}

    # ------------------------------------------------------------
    # 4. Capital-mark anchors, from the precomposed capitals;
    #    then the mark-axis rule: symmetric above marks with
    #    k != K get their anchor X on their own axis
    # ------------------------------------------------------------
    for line in patch_cap_mark_anchors(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")
    for line in patch_mark_axis(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")

    # ------------------------------------------------------------
    # 5. Normalize designer-set anchor Y values
    #    Semibold's capitals move to the capital reference (stage 4
    #    has already moved the .cap mark anchors to match). Anchors
    #    within 5 of a Y reference snap to it; others are reported.
    # ------------------------------------------------------------
    for line in normalize_anchor_y(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")
    snapshots.append(("normalized", _base_anchors(ttfont, lookup_index)))

    # ------------------------------------------------------------
    # 6. Heuristic anchors: the anchor-model candidate for each
    #    Latin/IPA base still lacking an above or below anchor
    # ------------------------------------------------------------
    for line in patch_anchors_heuristic(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")
    snapshots.append(("heuristic", _base_anchors(ttfont, lookup_index)))

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
    snapshots.append(("curated", _base_anchors(ttfont, lookup_index)))

    # ------------------------------------------------------------
    # 7b. Stem-axis rule: i ı j ȷ l get their anchor X on the axis
    #     of their stem, over designer and curated anchors alike
    # ------------------------------------------------------------
    for line in patch_stem_axis(ttfont, font_key, lookup_index):
        print(f"[{font_key}] {line}")
    snapshots.append(("stem", _base_anchors(ttfont, lookup_index)))

    # ------------------------------------------------------------
    # 8. Derived letters inherit their base letter's anchor, plus the
    #    outline shift (data/derived_letters.py)
    # ------------------------------------------------------------
    derived_set = set()
    for line in patch_derived_anchors(ttfont, font_key, lookup_index, touched=derived_set):
        print(f"[{font_key}] {line}")
    snapshots.append(("derived", _base_anchors(ttfont, lookup_index)))

    # ------------------------------------------------------------
    # 9. Patch precomposed anchors
    # ------------------------------------------------------------
    report_above = patch_precomposed_anchors(ttfont, font_key, 0, lookup_index)
    report_below = patch_precomposed_anchors(ttfont, font_key, 2, lookup_index)

    for line in report_above + report_below:
        print(f"[{font_key}] {line}")

    snapshots.append(("precomposed", _base_anchors(ttfont, lookup_index)))

    PROVENANCE_DIR.mkdir(exist_ok=True)
    owners = _owners(snapshots, {"curated": _curated_bases(font_key, cmap), "derived": derived_set})
    lines = [f"{json.dumps(glyph)}: {json.dumps(classes)}" for glyph, classes in owners.items()]
    (PROVENANCE_DIR / f"{font_key}.json").write_text(
        "{\n" + ",\n".join(lines) + "\n}\n", encoding="utf-8")

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
