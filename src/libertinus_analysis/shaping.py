#!/usr/bin/env python3

import unicodedata

from fontTools.ttLib import TTFont
import uharfbuzz as hb

from data.constants import (
    fonts,
    base_groups,
    mark_groups,
    superscript_consonant,
    mark_above_superscript_consonant,
    ipa_diacritic_bases,
)

# HARFBUZZ SHAPING

def shape_pair(hb_font, base_cp, mark_cp):
    """Shape a base+mark pair with HarfBuzz and return (infos, positions)."""
    text = chr(base_cp) + chr(mark_cp)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)
    return buf.glyph_infos, buf.glyph_positions

# GPOS MARK-TO-BASE EXTRACTION

def extract_mark_attachment_data(font, lookup_index):
    """
    Returns:
        mark_class_by_glyph: mark glyphName → classID
        anchors_by_base_glyph: base glyphName → {classID: anchor}
        cmap: Unicode → glyphName
    """
    cmap = font.getBestCmap()
    gpos = font["GPOS"].table
    lookup = gpos.LookupList.Lookup[lookup_index]

    mark_class_by_glyph = {}
    anchors_by_base_glyph = {}

    for sub in lookup.SubTable:
        if sub.LookupType != 4:
            continue

        # MARK ARRAY
        mark_records = sub.MarkArray.MarkRecord
        mark_glyphs = sub.MarkCoverage.glyphs

        for i, glyph in enumerate(mark_glyphs):
            mark_class_by_glyph[glyph] = mark_records[i].Class

        # BASE ARRAY
        base_records = sub.BaseArray.BaseRecord
        base_glyphs = sub.BaseCoverage.glyphs

        for i, glyph in enumerate(base_glyphs):
            baserec = base_records[i]
            anchors = {}
            for classID, anchor in enumerate(baserec.BaseAnchor):
                if anchor is not None:
                    anchors[classID] = anchor
            anchors_by_base_glyph[glyph] = anchors

    return mark_class_by_glyph, anchors_by_base_glyph, cmap

# CLASSIFICATION HELPERS

def missing_glyph(cp, cmap):
    """Return True if cp is not mapped in cmap."""
    return cmap.get(cp) is None


def missing_precomposed(base_cp, mark_cp, cmap):
    """
    Return True if NFC(base+mark) is a single codepoint that is not in cmap.
    """
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)
    if len(nfc) == 1:
        composed_cp = ord(nfc)
        return cmap.get(composed_cp) is None
    return False

def detect_substitution(base_cp, mark_cp, infos, cmap, font):
    """
    Detect whether GSUB substituted either base or mark glyph.
    """
    base_name = cmap.get(base_cp)
    mark_name = cmap.get(mark_cp)

    in_base_gid = font.getGlyphID(base_name) if base_name else None
    in_mark_gid = font.getGlyphID(mark_name) if mark_name else None

    out_base_gid = infos[0].codepoint
    out_mark_gid = infos[1].codepoint if len(infos) > 1 else None

    base_subbed = (in_base_gid is not None and out_base_gid != in_base_gid)
    mark_subbed = (in_mark_gid is not None and out_mark_gid != in_mark_gid)

    return base_subbed or mark_subbed


def has_anchor(base_cp, classID, anchors_by_base_glyph, cmap):
    """
    Return True if base_cp has an anchor for classID in anchors_by_base_glyph.
    """
    base_name = cmap.get(base_cp)
    if base_name is None:
        return False
    if base_name not in anchors_by_base_glyph:
        return False
    return classID in anchors_by_base_glyph[base_name]


def classify_combo(base_cp, mark_cp, classID,
                   cmap, anchors_by_base_glyph, hb_font, ttfont):
    """
    Returns (kind, infos, positions)
    kind in {"missing", "missing_precomposed", "precomposed",
            "substituted", "anchored", "fallback"}
    """

    # 1. Missing glyphs
    if missing_glyph(base_cp, cmap) or missing_glyph(mark_cp, cmap):
        return "missing", None, None

    # 2. Missing precomposed
    if missing_precomposed(base_cp, mark_cp, cmap):
        return "missing_precomposed", None, None

    # 3. Shape
    infos, positions = shape_pair(hb_font, base_cp, mark_cp)

    # 4. GSUB substitution
    if detect_substitution(base_cp, mark_cp, infos, cmap, ttfont):
        return "substituted", infos, positions

    # 5. True precomposed Unicode character
    if len(infos) == 1:
        seq = chr(base_cp) + chr(mark_cp)
        nfc = unicodedata.normalize("NFC", seq)
        if len(nfc) == 1 and ord(nfc) in cmap:
            return "precomposed", infos, positions

    # 6. Anchored vs fallback
    if has_anchor(base_cp, classID, anchors_by_base_glyph, cmap):
        return "anchored", infos, positions
    else:
        return "fallback", infos, positions

def classify_combo_sanity(base_cp, mark_cp, classID,
                          cmap, anchors_by_base_glyph, hb_font, ttfont):
    """
    Sanity classifier for IPA-relevant combining marks.

    Returns:
        kind in {"unsupported", "precomposed", "anchored", "fallback"}
        flags = {
            "missing_base": bool,
            "missing_mark": bool,
            "missing_precomposed": bool,
            "gsub_substitution": bool,
        }
        infos, positions = HarfBuzz shaping results
    """

    # Initialize flags
    flags = {
        "missing_base": False,
        "missing_mark": False,
        "missing_precomposed": False,
        "gsub_substitution": False,
    }

    # Semantic support: is this combination used in IPA notation?
    #    (We assume mark_cp is always a key in ipa_diacritic_bases.)
    supported_bases = ipa_diacritic_bases.get(mark_cp, [])
    supported = base_cp in supported_bases

    # Missing glyphs (base or mark)
    if missing_glyph(base_cp, cmap):
        flags["missing_base"] = True

    if missing_glyph(mark_cp, cmap):
        flags["missing_mark"] = True

    # If either glyph is missing, the combination cannot be realized.
    # Even if linguistically supported, the font cannot support it.
    if flags["missing_base"] or flags["missing_mark"]:
        kind = "unsupported"
        # Still shape something for grid integrity, but infos/positions
        # may be meaningless. We return them anyway for consistency.
        infos, positions = shape_pair(hb_font, base_cp, mark_cp)
        return kind, flags, infos, positions

    # Shape the pair with HarfBuzz
    infos, positions = shape_pair(hb_font, base_cp, mark_cp)

    # GSUB substitution detection
    if detect_substitution(base_cp, mark_cp, infos, cmap, ttfont):
        flags["gsub_substitution"] = True

    # Precomposed Unicode character
    seq = chr(base_cp) + chr(mark_cp)
    nfc = unicodedata.normalize("NFC", seq)

    if len(nfc) == 1:
        composed_cp = ord(nfc)
        if cmap.get(composed_cp) is not None:
            # True precomposed support
            kind = "precomposed"
            # Semantic override: if not linguistically supported, force unsupported
            if not supported:
                kind = "unsupported"
            return kind, flags, infos, positions
        else:
            # Precomposed exists in Unicode but missing in font
            flags["missing_precomposed"] = True

    # Anchored vs fallback
    if has_anchor(base_cp, classID, anchors_by_base_glyph, cmap):
        kind = "anchored"
    else:
        kind = "fallback"

    # Semantic override: unsupported combinations
    if not supported:
        kind = "unsupported"

    return kind, flags, infos, positions

# TEX RENDERING HELPERS

def tex(cp: int) -> str:
    return f'\\char"{cp:04X}'

def tex_prec(s): return f"\\PREC{{{s}}}"
def tex_anch(s): return f"\\ANCH{{{s}}}"
def tex_fall(s): return f"\\FALL{{{s}}}"
def tex_gsub(s): return f"\\GSUB{{{s}}}"
def tex_nobm(s): return f"\\NOBM{{{s}}}"
def tex_nopr(s): return f"\\NOPR{{{s}}}"


def render_cell(base_cp, mark_cp, kind, infos):
    """
    Render a single grid cell as TeX, wrapping the base+mark sequence
    in the appropriate macro based on kind.
    """
    # TeX payload: always original Unicode, never glyph IDs.
    if infos is None:
        # Missing cases: only the base is meaningful.
        raw = tex(base_cp)
    else:
        # All non-missing cases: show base + mark sequence.
        raw = tex(base_cp) + tex(mark_cp)

    if kind == "missing":
        return tex_nobm(raw)
    if kind == "missing_precomposed":
        return tex_nopr(raw)
    if kind == "precomposed":
        return tex_prec(raw)
    if kind == "substituted":
        return tex_gsub(raw)
    if kind == "anchored":
        return tex_anch(raw)
    if kind == "fallback":
        return tex_fall(raw)

    raise ValueError("Unknown kind")


def render_cell_sanity(base_cp, mark_cp, kind, flags):
    # If the mark is missing, suppress it entirely.
    if flags.get("missing_mark"):
        raw = tex(base_cp)
    else:
        raw = tex(base_cp) + tex(mark_cp)

    # Base wrapper by kind (color only)
    if kind == "unsupported":
        wrapped = f"\\UNSUPP{{{raw}}}"
    elif kind == "precomposed":
        wrapped = f"\\PREC{{{raw}}}"
    elif kind == "anchored":
        wrapped = f"\\ANCH{{{raw}}}"
    elif kind == "fallback":
        wrapped = f"\\FALL{{{raw}}}"
    else:
        raise ValueError(f"Unknown sanity kind: {kind}")

    # Flag cues (glyph-preserving, tabular-safe)
    if flags.get("gsub_substitution"):
        wrapped = f"\\GSUBOVERLAY{{{wrapped}}}"

    if flags.get("missing_precomposed"):
        wrapped = f"\\MISSINGPRE{{{wrapped}}}"

    if flags.get("missing_base") or flags.get("missing_mark"):
        wrapped = f"\\MISSINGGLYPH{{{wrapped}}}"

    return wrapped

# GRID GENERATION

def emit_mark_row(mark_cp, bases, classID,
                  cmap, anchors_by_base_glyph, hb_font, ttfont):
    """
    Emit one TeX row for a given mark over all bases.
    """
    cells = []
    for b in bases:
        kind, infos, positions = classify_combo(
            b, mark_cp, classID, cmap, anchors_by_base_glyph, hb_font, ttfont
        )
        cells.append(render_cell(b, mark_cp, kind, infos))
    return " ".join(cells)


def build_grid_tex(bases, marks, classID,
                   cmap, anchors_by_base_glyph, hb_font, ttfont):
    """
    Build the full TeX grid body (rows separated by blank lines).
    """
    rows = []
    for m in marks:
        rows.append(emit_mark_row(m, bases, classID,
                                  cmap, anchors_by_base_glyph, hb_font, ttfont))
        rows.append("")
    return "\n".join(rows)


def emit_grid_chunk(section_label, style, base_group_name, mark_group_name,
                    bases, marks, classID,
                    cmap, anchors_by_base_glyph, hb_font, ttfont):
    """
    Emit a complete TeX subsection for one (style, base group, mark group).
    """

    # Page break for large mark groups
    if len(marks) > 5:
        print(r"\newpage")

    # Subsection header
    print(rf"\subsection*{{{section_label}, {base_group_name}, {mark_group_name}}}")
    print()

    # Determine whether this chunk needs grouping braces
    # Style is explicit and machine-readable
    needs_group = style in {
        "italic",
        "bold",
        "bold_italic",
    }

    # Emit opening brace + style commands if needed
    if needs_group:
        if style == "italic":
            print(r"{\itshape")
        elif style == "bold":
            print(r"{\bfseries")
        elif style == "bold_italic":
            print(r"{\bfseries\itshape")

    # Emit grid
    print("% grid. columns are bases, rows are marks.")
    print(build_grid_tex(
        bases, marks, classID,
        cmap, anchors_by_base_glyph, hb_font, ttfont
    ))

    # Close grouping brace if needed
    if needs_group:
        print("}")


# HIGH-LEVEL EMITTERS

def print_combo(base_group, mark_group):
    """
    For a single base_group and mark_group, emit grids for all styles in fonts.
    """    
    for key, entry in mark_groups.items():
        if entry["items"] is mark_group:
            mark_group_name = entry["label"]
            classID = entry["classID"]
            break
    else:
        raise ValueError("mark_group not found")

    for key, entry in base_groups.items():
        if entry["items"] is base_group:
            base_group_name = entry["label"]
            break

    for style_key, info in fonts.items():
        font = TTFont(info["path"])
        fontdata = font.reader.file.getvalue()
        hb_face = hb.Face(fontdata)
        hb_font = hb.Font(hb_face)

        mark_class_by_glyph, anchors_by_base_glyph, cmap = \
            extract_mark_attachment_data(font, info["lookup_index"])

        emit_grid_chunk(
            section_label=info["label"],
            style=info["style"],
            base_group_name=base_group_name,
            mark_group_name=mark_group_name,
            bases=base_group,
            marks=mark_group,
            classID=classID,
            cmap=cmap,
            anchors_by_base_glyph=anchors_by_base_glyph,
            hb_font=hb_font,
            ttfont=font,
        )

        font.close()


def print_combos(base_lists, mark_lists):
    """
    Emit grids for all combinations of base_lists × mark_lists.
    """
    for bases in base_lists:
        for marks in mark_lists:
            print_combo(bases, marks)


def print_ipa_diacritics():
    """
    Emit IPA diacritic test grids using the same machinery as print_combo().
    """
    classID = 0

    styles = [
        "regular",
        "italic",
        "semibold",
        "semibold_italic",
    ]

    for style_key in styles:
        info = fonts[style_key]
        # Load font + HarfBuzz face
        font = TTFont(info["path"])
        fontdata = font.reader.file.getvalue()
        hb_face = hb.Face(fontdata)
        hb_font = hb.Font(hb_face)

        # Extract GPOS mark-to-base data
        mark_class_by_glyph, anchors_by_base_glyph, cmap = \
            extract_mark_attachment_data(font, info["lookup_index"])

        # Emit one subsection per style
        print(rf"\subsection*{{IPA diacritics -- {info['label']}}}")
        print()

        # Style wrapper
        needs_group = info["style"] in {"italic", "bold", "bold_italic"}
        if needs_group:
            if info["style"] == "italic":
                print(r"{\itshape")
            elif info["style"] == "bold":
                print(r"{\bfseries")
            elif info["style"] == "bold_italic":
                print(r"{\bfseries\itshape")

        # For each combining mark, emit a grid row
        for mark_cp, base_list in ipa_diacritic_bases.items():
            print(f"% Mark U+{mark_cp:04X}")
            print(build_grid_tex(
                bases=base_list,
                marks=[mark_cp],
                classID=classID,
                cmap=cmap,
                anchors_by_base_glyph=anchors_by_base_glyph,
                hb_font=hb_font,
                ttfont=font,
            ))
            print()

        if needs_group:
            print("}")

        print()
        font.close()
        