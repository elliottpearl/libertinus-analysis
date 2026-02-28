#!/bin/bash
for style in regular italic semibold semibold_italic
do
  echo "=== $style ==="
  for tag in has_left_weight has_right_weight is_symmetric has_overhang_right
  do
    printf "  %s true:  " "$tag"
    grep -R "\"$tag\": *true"  data/fontmetrics/$style.json | wc -l

    printf "  %s false: " "$tag"
    grep -R "\"$tag\": *false" data/fontmetrics/$style.json | wc -l
  done
  echo
done
