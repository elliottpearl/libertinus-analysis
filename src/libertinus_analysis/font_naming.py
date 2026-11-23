"""Give every font this project builds from Libertinus its own internal name.

The patched, draft and test fonts are Modified Versions of Libertinus Serif
under the OFL. "Libertinus" is not a Reserved Font Name, but the OFL FAQ asks
that a modified font not present itself under the original's name, so that it
is not confused with (or installed over) the original. Each build is renamed
from its file name:

    LibertinusSerif-SemiboldItalic-patch.otf        -> Libertinus Serif Patch
    LibertinusSerif-Regular-patch-nodot.otf         -> Libertinus Serif Patch Nodot
    LibertinusSerif-Italic-draft-merged.otf         -> Libertinus Serif Draft Merged

The style part of the names is kept as the designer set it. The rename is
idempotent and works on a font that was already renamed (a -nodot font is
built from the -patch font). LaTeX loads the fonts by file name, so nothing
depends on the family name.

Every font-writing path calls `save_renamed` instead of `TTFont.save`.
"""
from __future__ import annotations

from pathlib import Path

from fontTools.ttLib import TTFont

DESCRIPTION = (
    "Modified version of Libertinus Serif, built by libertinus-analysis "
    "(combining-mark anchor patch and test builds). Not an official Libertinus release."
)


def build_names(path: str | Path) -> tuple[str, str]:
    """(family, PostScript family) for an output file such as
    LibertinusSerif-Regular-patch-nodot.otf."""
    stem = Path(path).stem
    parts = stem.split("-", 2)
    if len(parts) == 3 and parts[0] == "LibertinusSerif":
        build = parts[2]
    else:
        # An ad hoc test build (e.g. semibold_italic-y0.otf): name it by the whole stem.
        build = "test-" + stem
    tokens = build.replace("_", "-").replace("#", "-").split("-")
    words = [w[:1].upper() + w[1:] for w in tokens if w]
    return "Libertinus Serif " + " ".join(words), "LibertinusSerif" + "".join(words)


def rename_font(ttfont: TTFont, path: str | Path) -> None:
    """Rename `ttfont` in its name table and CFF top dict for output `path`."""
    family, ps_family = build_names(path)
    cff = ttfont["CFF "].cff
    top = cff.topDictIndex[0]
    old_family = top.FamilyName
    old_ps_family = cff.fontNames[0].split("-", 1)[0]

    def swap(text: str) -> str:
        # PostScript-style names first: "LibertinusSerif-..." has no space.
        text = text.replace(old_ps_family + "-", ps_family + "-")
        if text == old_family or text.startswith(old_family + " "):
            text = family + text[len(old_family):]
        return text

    name = ttfont["name"]
    for rec in name.names:
        if rec.nameID in (1, 3, 4, 6, 16):
            rec.string = swap(rec.toUnicode())
    name.setName(DESCRIPTION, 10, 3, 1, 0x409)

    cff.fontNames[0] = swap(cff.fontNames[0])
    top.FamilyName = swap(top.FamilyName)
    top.FullName = swap(top.FullName)


def save_renamed(ttfont: TTFont, path: str | Path) -> None:
    rename_font(ttfont, path)
    ttfont.save(str(path))
