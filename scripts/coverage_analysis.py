# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Analyze coverage gaps in ontology.py by examining uncovered lines."""

import defusedxml.ElementTree as DefusedElementTree

tree = DefusedElementTree.parse("coverage.xml")
root = tree.getroot()

for cls in root.iter("class"):
    filename = cls.get("filename", "")
    if "ontology" not in filename:
        continue
    print(f"\n=== {filename} (line_rate={cls.get('line-rate')}) ===")

    missing_lines = [int(line.get("number", 0)) for line in cls.iter("line") if line.get("hits") == "0"]

    if missing_lines:
        # Group contiguous ranges
        ranges = []
        start = missing_lines[0]
        end = missing_lines[0]
        for ln in missing_lines[1:]:
            if ln == end + 1:
                end = ln
            else:
                ranges.append((start, end))
                start = ln
                end = ln
        ranges.append((start, end))

        print(f"Total uncovered lines: {len(missing_lines)}")
        print(f"Uncovered ranges ({len(ranges)} groups):")
        for s, e in ranges:
            if s == e:
                print(f"  Line {s}")
            else:
                print(f"  Lines {s}-{e} ({e - s + 1} lines)")

# Also check algebra.py
for cls in root.iter("class"):
    filename = cls.get("filename", "")
    if "algebra" not in filename:
        continue
    print(f"\n=== {filename} (line_rate={cls.get('line-rate')}) ===")

    missing_lines = [int(line.get("number", 0)) for line in cls.iter("line") if line.get("hits") == "0"]

    if missing_lines:
        ranges = []
        start = missing_lines[0]
        end = missing_lines[0]
        for ln in missing_lines[1:]:
            if ln == end + 1:
                end = ln
            else:
                ranges.append((start, end))
                start = ln
                end = ln
        ranges.append((start, end))

        print(f"Total uncovered lines: {len(missing_lines)}")
        print(f"Uncovered ranges ({len(ranges)} groups):")
        for s, e in ranges:
            if s == e:
                print(f"  Line {s}")
            else:
                print(f"  Lines {s}-{e} ({e - s + 1} lines)")
