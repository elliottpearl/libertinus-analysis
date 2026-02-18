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
# Classic classifier renderer
# ----------------------------------------------------------------------

def render_cell(base_cp, mark_cp, kind, infos):
    """
    Render a single grid cell for the classic classifier.

    kind ∈ {
        "missing",
        "missing_precomposed",
        "precomposed",
        "substituted",
        "anchored",
        "fallback"
    }

    The classic classifier does not track semantic support or GSUB
    expectations, so only the basic categories are surfaced.
    """

    # Missing cases: only the base is meaningful.
    if infos is None:
        raw = tex(base_cp)
    else:
        raw = tex(base_cp) + tex(mark_cp)

    if kind == "missing":
        return _wrap("MISSINGGLYPH", raw)

    if kind == "missing_precomposed":
        return _wrap("UNSUPPORTEDPREC", raw)

    if kind == "precomposed":
        return _wrap("SUPPORTEDPREC", raw)

    if kind == "substituted":
        # Substitution is not a semantic category; treat as anchored.
        return _wrap("SUPPORTEDANCH", raw)

    if kind == "anchored":
        return _wrap("SUPPORTEDANCH", raw)

    if kind == "fallback":
        return _wrap("SUPPORTEDFALL", raw)

    raise ValueError(f"Unknown kind: {kind}")

# ----------------------------------------------------------------------
# Sanity classifier renderer
# ----------------------------------------------------------------------

def render_cell_sanity(base_cp, mark_cp, kind, flags):
    """
    Render a TeX cell for the IPA sanity classifier.

    kind ∈ {
        "unsupported",
        "precomposed",
        "anchored",
        "fallback"
    }

    flags is a dict:
        {
            "missing_base": bool,
            "missing_mark": bool,
            "missing_precomposed": bool,

            "gsub_prec_expected": bool,
            "gsub_prec_occurred": bool,

            "gsub_dotless_expected": bool,
            "gsub_dotless_occurred": bool,

            "gsub_altcap_expected": bool,
            "gsub_altcap_occurred": bool,

            "dotless_failure_significant": bool,

            "supported": bool,
        }

    This renderer chooses exactly one semantic macro per cell.
    Missing glyphs override everything. GSUB failures override
    semantic color with green/light-green. Otherwise, supported/
    unsupported by kind determines the macro.
    """

    # Missing mark → show base only
    if flags.get("missing_mark"):
        raw = tex(base_cp)
    else:
        raw = tex(base_cp) + tex(mark_cp)

    # Missing glyphs override everything
    if flags.get("missing_base") or flags.get("missing_mark"):
        return _wrap("MISSINGGLYPH", raw)

    # ------------------------------------------------------------------
    # GSUB failure override (new logic)
    #
    # Precomposed GSUB failure → green
    # Dotless GSUB failure → green *only if significant*
    # Alt-cap GSUB failure → green
    # ------------------------------------------------------------------

    gsub_failure = (
        (flags.get("gsub_prec_expected") and not flags.get("gsub_prec_occurred"))
        or flags.get("dotless_failure_significant")
        or (flags.get("gsub_altcap_expected") and not flags.get("gsub_altcap_occurred"))
    )

    if gsub_failure:
        if flags.get("supported"):
            return _wrap("GSUBFAILSUPPORTED", raw)
        else:
            return _wrap("GSUBFAILUNSUPPORTED", raw)

    # ------------------------------------------------------------------
    # Semantic support
    # ------------------------------------------------------------------

    supported = flags.get("supported", False)

    # ------------------------------------------------------------------
    # Choose semantic macro
    # ------------------------------------------------------------------

    if supported:
        if kind == "precomposed":
            macro = "SUPPORTEDPREC"
        elif kind == "anchored":
            macro = "SUPPORTEDANCH"
        elif kind == "fallback":
            macro = "SUPPORTEDFALL"
        else:
            macro = "UNSUPPORTEDFALL"
    else:
        if kind == "precomposed":
            macro = "UNSUPPORTEDPREC"
        elif kind == "anchored":
            macro = "UNSUPPORTEDANCH"
        elif kind == "fallback":
            macro = "UNSUPPORTEDFALL"
        else:
            macro = "UNSUPPORTEDFALL"

    return _wrap(macro, raw)
    