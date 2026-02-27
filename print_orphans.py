#!/usr/bin/env python3
import json

with open("data/fontmetrics/regular.json", "r", encoding="utf-8") as f:
    data = json.load(f)

orphans = sorted(data.get("_orphans", {}).keys())

for g in orphans:
    print(g)
