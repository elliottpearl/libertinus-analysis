# Font loading and fontspec

Fonts are in `fonts/` as `.otf` and `.ttf` fonts. 
This includes original fonts (LIbertinus, Gentium Plus, Noto) and patches of Libertinus.
LSP uses the semibold Libertinus font for boldface.

LaTeX files are in `tex/`.  

Always include the extension `.otf` and `.ttf` in the font loading command in LaTeX.

```
\usepackage{fontspec}

% Load fonts
% always use `Path = ../fonts/,`
% always include extension e.g. `.otf`, `.ttf`

\setmainfont{Libertinus Serif}[
	Path = ../fonts/,
	UprightFont    = LibertinusSerif-Regular.otf,
	ItalicFont     = LibertinusSerif-Italic.otf,
	BoldFont       = LibertinusSerif-Semibold.otf,
	BoldItalicFont = LibertinusSerif-SemiboldItalic.otf
]

\newfontfamily\Gentium[
	Path = ../fonts/,
]{GentiumPlus-Regular.ttf}
```
