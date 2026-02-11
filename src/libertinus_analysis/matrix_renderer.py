class MatrixRenderer:
    def __init__(
        self,
        marks,
        bases,
        classification,
        fonts,
        layout="tabular",
    ):
        self.marks = marks
        self.bases = bases
        self.classification = classification
        self.fonts = fonts
        self.layout = layout

    def latex_table(self):
        """Return a LaTeX tabular environment as a string."""
        rows = []
        # TODO: fill in using your existing print_combos logic
        return "\n".join(rows)