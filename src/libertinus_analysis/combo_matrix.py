# combo_matrix.py

from fontTools.ttLib import TTFont
import uharfbuzz as hb

from .font_context import FontContext
from .classifiers import (
    classify_combo_classic,
    classify_combo_sanity,
    classify_combo_plain,
)
from .tex_helpers import render_cell_classic, render_cell, latex_font_cmd
from .ipa_loader import unicode_groups, mark_class_index


class ComboMatrix:
    """
    A reusable engine for classifying mark-base combinations across fonts
    and emitting LaTeX in several formats.

    Public builders:
        - latex_grid()
        - latex_paragraph()
    """

    def __init__(self, base_groups, mark_groups, fonts, classifier):
        self.base_groups = base_groups
        self.mark_groups = mark_groups
        self.fonts = fonts

        # classifier is one of:
        #   classify_combo_classic
        #   classify_combo_sanity
        #   classify_combo_plain
        self.classifier = classifier

        self.font_contexts = {}
        self.grid = {}

    # Font loading and classification

    def load_fonts(self):
        """Load all fonts and build FontContext objects."""
        for font_key, info in self.fonts.items():
            self.font_contexts[font_key] = FontContext.from_path(
                path=info["path"],
                lookup_index=info["lookup_index"],
                font_key=font_key,
            )
        return self

    def classify(self):
        """
        Classify all mark/base pairs for all fonts.

        The classifier returns:
            - classic: (kind, infos, positions)
            - sanity/plain: (kind, flags, infos, positions)
        """
        for font_key, info in self.fonts.items():
            fontctx = self.font_contexts[font_key]

            for mark_group in self.mark_groups.values():
                for mark_cp in mark_group["items"]:
                    classIndex = mark_class_index.get(mark_cp)

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

    # Internal helpers for building LaTeX

    def _emit_mark_row(self, mark_cp, bases, font_key):
        """
        Emit one row of TeX cells for a given mark across all bases.
        Rendering is delegated to the appropriate renderer.
        """
        cells = []

        for base_cp in bases:
            result = self.grid.get((mark_cp, base_cp, font_key))

            if result is None:
                # Legacy fallback
                if self.classifier is classify_combo_classic:
                    result = ("fallback", None, None)
                else:
                    result = ("fallback", {}, None, None)

            if self.classifier is classify_combo_classic:
                kind, infos, positions = result
                cell = render_cell_classic(base_cp, mark_cp, kind, infos)

            elif self.classifier in (classify_combo_sanity, classify_combo_plain):
                kind, flags, infos, positions = result
                cell = render_cell(base_cp, mark_cp, kind, flags)

            else:
                raise ValueError(f"Unknown classifier: {self.classifier}")

            cells.append(cell)

        return " ".join(cells)

    def _build_grid_body(self, marks, bases, font_key):
        rows = []
        for m in marks:
            rows.append(self._emit_mark_row(m, bases, font_key))
            rows.append("")
        return "\n".join(rows)

    def _build_latex_grid_for_font(self, marks, bases, font_key, section_label=None):
        info = self.fonts[font_key]
        label = section_label or info["label"]

        out = []

        if len(marks) > 5:
            out.append(r"\newpage")

        out.append(rf"\subsection*{{{label}}}")
        out.append("")

        cmd, needs_group = latex_font_cmd(font_key)

        if needs_group:
            out.append("{" + cmd)

        out.append("% grid. columns are bases, rows are marks.")
        out.append(self._build_grid_body(marks, bases, font_key))

        if needs_group:
            out.append("}")

        return "\n".join(out)

    # Public builders

    def latex_grid(self):
        out = []

        for base_group_key, base_group in self.base_groups.items():
            base_label = unicode_groups[base_group_key]["label"]

            for mark_group_key, mark_group in self.mark_groups.items():
                mark_label = unicode_groups[mark_group_key]["label"]

                marks = mark_group["items"]
                bases = base_group["items"]

                for font_key in self.fonts:
                    font_label = self.fonts[font_key]["label"]

                    section_label = f"{font_label}, {base_label}, {mark_label}"

                    out.append(
                        self._build_latex_grid_for_font(
                            marks=marks,
                            bases=bases,
                            font_key=font_key,
                            section_label=section_label,
                        )
                    )

        return "\n\n".join(out)

    def latex_paragraph(self):
        out = []

        for mark_group in self.mark_groups.values():
            for mark_cp in mark_group["items"]:
                for font_key in self.fonts:
                    bases = []
                    for base_group in self.base_groups.values():
                        bases.extend(base_group["items"])

                    paragraph = self._build_latex_grid_for_font(
                        marks=[mark_cp],
                        bases=bases,
                        font_key=font_key,
                        section_label=f"U+{mark_cp:04X}",
                    )
                    out.append(paragraph)

        return "\n\n".join(out)
