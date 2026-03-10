# tex_helpers.py
#
# Basic TeX emitters for Unicode codepoints and semantic wrappers.
# Emits exactly one macro per cell, with no nested color wrappers.
# All color decisions are handled by the LaTeX macro layer.

def tex(cp):
    """Return TeX code for a Unicode codepoint."""
    return f'\\char"{cp:04X}'


def _wrap(macro, raw):
    """Wrap the raw TeX payload in a single semantic macro."""
    return f"\\{macro}{{{raw}}}"


# ----------------------------------------------------------------------
# Shared LaTeX font command helper (factored out of ComboMatrix)
# ----------------------------------------------------------------------

def latex_font_cmd(font_key):
    """
    Return (cmd, needs_group) for the given font_key.
    """
    base = r""
    patch = r"\LibertinusSerifPatch"

    # Determine family
    if font_key.endswith("_patch"):
        family = patch
    else:
        family = base

    # Build command
    parts = [family]

    if "semibold" in font_key:
        parts.append(r"\bfseries")
    if "italic" in font_key:
        parts.append(r"\itshape")

    cmd = "".join(parts)

    # Group needed if anything beyond the bare family is used
    needs_group = (cmd != base)

    return cmd, needs_group


def latex_font_style(font_key, text):
    """
    Convenience wrapper: apply the LaTeX font style for font_key
    directly to the given text.

    This is ideal for report_fontmetrics.py, where each row is a
    single TeX fragment and grouping does not span multiple lines.
    """
    cmd, needs_group = latex_font_cmd(font_key)
    if needs_group:
        return f'{{{cmd} {text}}}'
    else:
        return f'{cmd}{text}'


# ----------------------------------------------------------------------
# Unified renderer for sanity/plain classifiers
# ----------------------------------------------------------------------

def render_cell(base_cp, mark_cp, kind, flags):
    """
    Render a TeX cell for the sanity/plain classifiers.

    kind ∈ {
        "precomposed",
        "anchored",
        "fallback"
    }

    flags is a dict:
        {
            "missing_base": bool,
            "missing_mark": bool,
            "missing_precomposed": bool,
            "supported": bool,
        }

    This renderer chooses exactly one semantic macro per cell.
    Missing glyphs override everything. Otherwise, supported/
    unsupported and kind determine the macro.
    """

    # Missing mark → show base only
    if flags.get("missing_mark"):
        raw = tex(base_cp)
    else:
        raw = tex(base_cp) + tex(mark_cp)

    # Missing glyphs override everything
    if flags.get("missing_base") or flags.get("missing_mark"):
        return _wrap("MISSINGGLYPH", raw)

    # Semantic support
    supported = flags.get("supported", False)

    # Choose semantic macro
    if supported:
        if kind == "precomposed":
            macro = "SUPPORTEDPREC"
        elif kind == "anchored":
            macro = "SUPPORTEDANCH"
        else:
            macro = "SUPPORTEDFALL"
    else:
        if kind == "precomposed":
            macro = "UNSUPPORTEDPREC"
        elif kind == "anchored":
            macro = "UNSUPPORTEDANCH"
        else:
            macro = "UNSUPPORTEDFALL"

    return _wrap(macro, raw)