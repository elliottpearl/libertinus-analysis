#!/bin/bash
# Save current directory
ORIG=$(pwd)

# Move into tex directory
cd tex

# Run xelatex on the file inside tex/
xelatex libertinus-analysis.tex

# Return to original directory
cd "$ORIG"
