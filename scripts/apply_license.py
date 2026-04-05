import glob

HEADER = """# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>
"""


def apply_header():
    py_files = set()
    for directory in ["src", "tests", "scripts"]:
        pattern = f"{directory}/**/*.py"
        py_files.update(glob.glob(pattern, recursive=True))

    for base in ["*.py"]:
        py_files.update(glob.glob(base))

    for filepath in py_files:
        if "apply_license.py" in filepath:
            continue
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")

            # Identify if there is an existing copyright header block at the very top.
            # We look at the first few lines to see if it starts with "# Copyright".
            has_copyright = any(line.startswith("# Copyright") for line in lines[:5])

            if has_copyright:
                # Remove the contiguous comment block at the top
                while lines and lines[0].startswith("#"):
                    lines.pop(0)

            # Reconstruct content
            # Ensure there is exactly one blank line after the header
            while lines and lines[0].strip() == "":
                lines.pop(0)

            new_content = HEADER + "\n" + "\n".join(lines)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Applied to {filepath}")
        except Exception as e:
            print(f"Error reading {filepath}: {e}")


if __name__ == "__main__":
    apply_header()
