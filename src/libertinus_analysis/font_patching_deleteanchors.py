# font_patching_deleteanchors.py
"""
Anchor-deletion stage of the Libertinus patching pipeline.

Deletes the designer-set above/below base anchors that the anchor audit
recorded as bad (data/fontanchors_audit/<font_key>.py, written by
run_anchor_audit.py), subject to the human overrides in
data/fontanchors_audit/overrides.py.

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

def anchors_to_delete(font_key: str):
    """
    Return {(glyph_name, classIndex)} for the anchors to delete:
    audited as bad and not overruled with "keep", or overruled with "delete".
    """
    audit = load_anchor_audit(font_key)
    overrides = load_audit_overrides(font_key)

    doomed = set()
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

def delete_bad_anchors(ttfont, font_key, lookup_index):
    """
    Delete the bad above/below base anchors from the MarkToBase lookup.

    Returns the list of (glyph_name, classIndex, (x, y)) actually deleted.
    """
    doomed = anchors_to_delete(font_key)

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

    print(f"[{font_key}] deleted {len(deleted)} bad anchors ({len(doomed)} listed)")
    return deleted
