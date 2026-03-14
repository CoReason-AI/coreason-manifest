# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at [https://prosperitylicense.com/versions/3.0.0](https://prosperitylicense.com/versions/3.0.0)
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: [https://github.com/CoReason-AI/coreason-manifest](https://github.com/CoReason-AI/coreason-manifest)

import re
import sys

FORBIDDEN_PATTERNS = [
    r"import\s+socket",
    r"from\s+socket\s+import",
    r"import\s+fastapi",
    r"from\s+fastapi\s+import",
    r"import\s+flask\b",
    r"from\s+flask\s+import",
    r"os\.mkdir",
    r"os\.makedirs",
    r"logger\.add",
]


def main() -> None:
    diff_content = sys.stdin.read()

    in_py_file = False
    added_lines = []

    for line in diff_content.splitlines():
        if line.startswith("+++ "):
            filename = line[4:].strip()
            filename = filename.removeprefix("b/")
            in_py_file = filename.endswith(".py")
            continue

        if in_py_file and line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])

    for added_line in added_lines:
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, added_line, re.IGNORECASE):
                print(f"Architectural Violation: Forbidden runtime artifact detected: {added_line}")
                sys.exit(1)

    print("Architecture evaluation passed: Passive by Design.")
    sys.exit(0)


if __name__ == "__main__":
    main()
