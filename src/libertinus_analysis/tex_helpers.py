def tex(cp):
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
