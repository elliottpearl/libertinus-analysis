#!/usr/bin/env python3
from fontTools.ttLib import TTFont

def unicode_cmap_dict(path):
    font = TTFont(path)
    mapping = {}
    for table in font["cmap"].tables:
        # Keep only Unicode subtables (platform 0, or Windows Unicode)
        if table.isUnicode():
            for code, name in table.cmap.items():
                mapping[code] = name
    return mapping

orig = unicode_cmap_dict("fonts/LibertinusSerif-Regular.otf")
patch = unicode_cmap_dict("fonts/LibertinusSerif-Regular-Indoeuropean.otf")

added = sorted(set(patch) - set(orig))
removed = sorted(set(orig) - set(patch))
changed = sorted(k for k in orig if k in patch and orig[k] != patch[k])

print("=== Added codepoints ===")
for k in added:
    print(f"U+{k:04X} → {patch[k]}")

print("\n=== Removed codepoints ===")
for k in removed:
    print(f"U+{k:04X} → {orig[k]}")

print("\n=== Changed mappings ===")
for k in changed:
    print(f"U+{k:04X}: {orig[k]} → {patch[k]}")
