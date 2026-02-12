from fontTools.ttLib import TTFont
import harfbuzz as hb

from .font_context import FontContext
from .font_helpers import extract_mark_attachment_data
from .classifiers import classify_combo, classify_combo_sanity
from .tex_helpers import render_cell, render_cell_sanity


class ComboMatrix:
    def __init__(self, base_groups, mark_groups, fonts, classifier):
        # Input groups and font metadata
        self.base_groups = base_groups
        self.mark_groups = mark_groups
        self.fonts = fonts
        self.classifier = classifier

        # Per-font contexts: style_key → FontContext
        self.font_contexts = {}

        # Classification results: (mark_cp, base_cp, font_key) → classifier output tuple
        self.grid = {}

        # Accumulated LaTeX output
        self.tables = []

    # Load all fonts and extract GPOS mark-to-base data
    def load_fonts(self):
        for style_key, info in self.fonts.items():
            self.font_contexts[style_key] = FontContext.from_path(
                path=info["path"],
                lookup_index=info["lookup_index"],
            )
        return self

    # Classify all mark/base pairs for all fonts
    def classify(self):
        for font_key, info in self.fonts.items():
            fontctx = self.font_contexts[font_key]

            for mark_group in self.mark_groups.values():
                for mark_cp in mark_group["items"]:
                    markGlyph = fontctx.cmap.get(mark_cp)
                    classIndex = fontctx.markClassByGlyph.get(markGlyph)

                    for base_group in self.base_groups.values():
                        for base_cp in base_group["items"]:
                            result = self.classifier(
                                base_cp,
                                mark_cp,
                                classIndex,
                                fontctx,
                            )
                            self.grid[(mark_cp, base_cp, font_key)] = result

        return self

    # Build one row of TeX cells for a given mark across all bases
    def _emit_mark_row(self, mark_cp, bases, font_key):
        cells = []
        for base_cp in bases:
            result = self.grid[(mark_cp, base_cp, font_key)]

            # classify_combo → (kind, infos, positions)
            # classify_combo_sanity → (kind, flags, infos, positions)
            if self.classifier is classify_combo:
                kind, infos, positions = result
                cell = render_cell(base_cp, mark_cp, kind, infos)
            else:
                kind, flags, infos, positions = result
                cell = render_cell_sanity(base_cp, mark_cp, kind, flags)

            cells.append(cell)

        return " ".join(cells)

    # Build the full grid body (rows separated by blank lines)
    def _build_grid_body(self, marks, bases, font_key):
        rows = []
        for m in marks:
            rows.append(self._emit_mark_row(m, bases, font_key))
            rows.append("")  # blank line between rows
        return "\n".join(rows)

    # Build a complete LaTeX grid for one font
    def _build_latex_grid(self, marks, bases, font_key, section_label=None):
        info = self.fonts[font_key]
        style = info["style"]
        label = section_label or info["label"]

        out = []

        # Page break for large mark groups
        if len(marks) > 5:
            out.append(r"\newpage")

        # Subsection header
        out.append(rf"\subsection*{{{label}}}")
        out.append("")

        # Style wrapper
        needs_group = style in {"italic", "bold", "bold_italic"}
        if needs_group:
            if style == "italic":
                out.append(r"{\itshape")
            elif style == "bold":
                out.append(r"{\bfseries")
            elif style == "bold_italic":
                out.append(r"{\bfseries\itshape")

        # Grid body
        out.append("% grid. columns are bases, rows are marks.")
        out.append(self._build_grid_body(marks, bases, font_key))

        if needs_group:
            out.append("}")

        return "\n".join(out)

    # Emit normal grids for one base/mark group across all fonts
    def latex_tabular(self, base_group, mark_group, section_label=None):
        for font_key in self.fonts:
            table = self._build_latex_grid(
                marks=mark_group["items"],
                bases=base_group["items"],
                font_key=font_key,
                section_label=section_label,
            )
            self.tables.append(table)
        return self

    # Emit all combinations of base_groups × mark_groups
    def emit_all_combos(self):
        for base_group in self.base_groups.values():
            for mark_group in self.mark_groups.values():
                self.latex_tabular(base_group, mark_group)
        return self

    # Emit IPA diacritic grids (one mark per subsection)
    def emit_ipa_diacritics(self, ipa_diacritic_bases):
        for font_key, info in self.fonts.items():
            self.tables.append(
                rf"\subsection*{{IPA diacritics -- {info['label']}}}"
            )

            needs_group = info["style"] in {"italic", "bold", "bold_italic"}
            if needs_group:
                wrapper = {
                    "italic": r"{\itshape",
                    "bold": r"{\bfseries",
                    "bold_italic": r"{\bfseries\itshape",
                }[info["style"]]
                self.tables.append(wrapper)

            for mark_cp, base_list in ipa_diacritic_bases.items():
                table = self._build_latex_grid(
                    marks=[mark_cp],
                    bases=base_list,
                    font_key=font_key,
                    section_label=f"U+{mark_cp:04X}",
                )
                self.tables.append(table)

            if needs_group:
                self.tables.append("}")

        return self
