# font_patching_deleteanchors.py
"""
Anchor-deletion stage of the Libertinus patching pipeline.

Deletes designer-set above/below base anchors, so that later stages can
replace them (stage 6 with the anchor-model candidate, stage 7 with a curated
anchor, stage 8 by inheritance). Two sources:

    - the human overrides in data/fontanchors_audit/overrides.py: "delete"
      always deletes, for any reason (a copied anchor, a collision, an anchor
      that does not fit the style's anchor model);
    - the anchor audit's "bad" verdicts (data/fontanchors_audit/<font_key>.py,
      written by run_anchor_audit.py), only if use_audit is true; "keep" in
      the overrides then saves an anchor from them.

Behavior:
    - Only base anchors of class 0 (above) and 2 (below) are touched.
    - "suspect" anchors are kept unless an override says "delete".
    - The BaseRecord itself is kept; only the anchor is set to None.
"""

# ------------------------------------------------------------
# Lazy loaders for the audit record and the overrides
# ------------------------------------------------------------

def load_anchor_audit(font_key: str):
    """
    Dynamically import data.fontanchors_audit.<font_key>
    and return its `audit` dict.
    """
    module_name = f"data.fontanchors_audit.{font_key}"
    mod = __import__(module_name, fromlist=["audit"])
    return mod.audit


def load_audit_overrides(font_key: str):
    mod = __import__("data.fontanchors_audit.overrides", fromlist=["overrides"])
    return mod.overrides.get(font_key, {})

# ------------------------------------------------------------
# Which anchors to delete
# ------------------------------------------------------------

def anchors_to_delete(font_key: str, use_audit: bool = True):
    """
    Return {(glyph_name, classIndex)} for the anchors to delete:
    overruled with "delete", or (if use_audit) audited as bad and not
    overruled with "keep".
    """
    overrides = load_audit_overrides(font_key)

    doomed = set()
    if use_audit:
        audit = load_anchor_audit(font_key)
        for glyph_name, class_map in audit.items():
            for classIndex, record in class_map.items():
                if record["verdict"] == "bad":
                    doomed.add((glyph_name, classIndex))

    for glyph_name, class_map in overrides.items():
        for classIndex, decision in class_map.items():
            if decision == "keep":
                doomed.discard((glyph_name, classIndex))
            elif decision == "delete":
                doomed.add((glyph_name, classIndex))
            else:
                raise ValueError(
                    f"overrides[{font_key!r}][{glyph_name!r}][{classIndex}]: "
                    f"expected 'keep' or 'delete', got {decision!r}"
                )
    return doomed

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def delete_bad_anchors(ttfont, font_key, lookup_index, use_audit=True):
    """
    Delete the bad above/below base anchors from the MarkToBase lookup.

    Returns the list of (glyph_name, classIndex, (x, y)) actually deleted.
    """
    doomed = anchors_to_delete(font_key, use_audit)

    gpos = ttfont["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    deleted = []
    for sub in lookup.SubTable:
        if sub.LookupType != 4:
            continue  # only MarkToBase

        for glyph_name, baserec in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
            for classIndex, anchor in enumerate(baserec.BaseAnchor):
                if anchor is None or (glyph_name, classIndex) not in doomed:
                    continue
                deleted.append((glyph_name, classIndex, (anchor.XCoordinate, anchor.YCoordinate)))
                baserec.BaseAnchor[classIndex] = None

    source = "overrides and audit" if use_audit else "overrides only"
    print(f"[{font_key}] deleted {len(deleted)} bad anchors ({len(doomed)} listed; {source})")
    return deleted
