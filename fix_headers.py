# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import os
import re

mandated_header = """# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>
"""

header_regex = re.compile(
    r"^# Copyright \(c\) \d{4} CoReason, Inc\.?\n"
    r"(?:#\n)?"
    r"# This software is proprietary and dual-licensed\.?\n"
    r"# Licensed under the Prosperity Public License 3\.0 \(the \"License\"\)\.?\n"
    r"# A copy of the license is available at (?:<)?https://prosperitylicense\.com/versions/3\.0\.0(?:>)?\n"
    r"# For details, see the LICENSE file\.?\n"
    r"# Commercial use beyond a 30-day trial requires a separate license\.?\n"
    r"#\n"
    r"# Source Code: (?:<)?https://github\.com/CoReason-AI/coreason-manifest(?:>)?\n",
    re.MULTILINE,
)


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    match = header_regex.search(content)
    if match:
        # Check if the matched header is already the mandated one
        if match.group(0) == mandated_header:
            return False  # Already correct

        # Replace the header
        new_content = content[: match.start()] + mandated_header + content[match.end() :]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated header in {filepath}")
        return True
    # Let's see if we can just prepend it
    if not content.startswith("# Copyright"):
        # Add to top
        print(f"Adding header to {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(mandated_header + "\n" + content)
        return True

    return False


for root, _, files in os.walk("."):
    if ".venv" in root or ".git" in root or ".ruff_cache" in root or ".pytest_cache" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))
