from fontTools.ttLib import TTFont
import uharfbuzz as hb

from .font_context import FontContext
from .font_helpers import extract_mark_attachment_data
from .classifiers import classify_combo, classify_combo_sanity
from .tex_helpers import render_cell, render_cell_sanity


class ComboMatrix:
    """
    A reusable engine for classifying mark-base combinations across fonts
    and emitting LaTeX in several formats.

    Public builders:
        - latex_grid()
        - latex_tabular()
        - latex_paragraph()
    """

    def __init__(self, base_groups, mark_groups, fonts, classifier):
        self.base_groups = base_groups
        self.mark_groups = mark_groups
        self.fonts = fonts
        self.classifier = classifier

        # Filled by load_fonts()
        self.font_contexts = {}

        # Filled by classify()
        # key: (mark_cp, base_cp, font_key) → classifier output tuple
        self.grid = {}

        # Font loading and classification
    
    def load_fonts(self):
        """Load all fonts and build FontContext objects."""
        for style_key, info in self.fonts.items():
            self.font_contexts[style_key] = FontContext.from_path(
                path=info["path"],
                lookup_index=info["lookup_index"],
                font_key=style_key,
            )
        return self

    def classify(self):
        """Classify all mark/base pairs for all fonts."""
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

    # Internal helpers for building LaTeX

    def _emit_mark_row(self, mark_cp, bases, font_key):
        """Emit one row of TeX cells for a given mark across all bases."""
        cells = []
        for base_cp in bases:
            result = self.grid.get((mark_cp, base_cp, font_key))
            if result is None:
                # Legacy behavior: treat missing combos as fallback
                result = ("fallback", None, None)

            if self.classifier is classify_combo:
                kind, infos, positions = result
                cell = render_cell(base_cp, mark_cp, kind, infos)
            else:
                kind, flags, infos, positions = result
                cell = render_cell_sanity(base_cp, mark_cp, kind, flags)

            cells.append(cell)

        return " ".join(cells)

    def _build_grid_body(self, marks, bases, font_key):
        """Build the full grid body (rows separated by blank lines)."""
        rows = []
        for m in marks:
            rows.append(self._emit_mark_row(m, bases, font_key))
            rows.append("")  # blank line between rows
        return "\n".join(rows)

    def _build_latex_grid_for_font(self, marks, bases, font_key, section_label=None):
        """Build a complete LaTeX grid for one font."""
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

    # Public builders

    def latex_grid(self):
        """
        Emit a grid-style report for all base_groups × mark_groups × fonts.
        Returns a single LaTeX string.
        """
        out = []
        for base_group in self.base_groups.values():
            for mark_group in self.mark_groups.values():
                marks = mark_group["items"]
                bases = base_group["items"]

                for font_key in self.fonts:
                    out.append(
                        self._build_latex_grid_for_font(
                            marks=marks,
                            bases=bases,
                            font_key=font_key,
                            section_label=None,
                        )
                    )
        return "\n\n".join(out)

    def latex_tabular(self):
        """
        Emit a tabular-style report (same content, different layout).
        Returns a single LaTeX string.
        """
        # For now, reuse the grid builder.
        # You can later replace this with a true tabular environment.
        return self.latex_grid()

    def latex_paragraph(self):
        """
        Emit an IPA-style paragraph report:
        - one mark per paragraph
        - bases inline
        - across all fonts
        """
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