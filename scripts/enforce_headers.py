# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

#!/usr/bin/env python3
import sys
from pathlib import Path

REQUIRED_HEADER = """# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>
"""


def check_and_fix_headers(files: list[str]) -> int:
    exit_code = 0
    for file_path in files:
        path = Path(file_path)
        if not path.is_file() or path.suffix != ".py":
            continue

        content = path.read_text()
        if not content.startswith(REQUIRED_HEADER):
            print(f"Fixing missing/incorrect header in: {file_path}")
            # Strip old headers if they exist but are wrong, or just prepend
            if content.startswith("# Copyright"):
                # Rough heuristic to remove old header block
                lines = content.splitlines()
                start_idx = 0
                for i, line in enumerate(lines):
                    if not line.startswith("#"):
                        start_idx = i
                        break
                content = "\n".join(lines[start_idx:]).lstrip()

            path.write_text(REQUIRED_HEADER + "\n" + content)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(check_and_fix_headers(sys.argv[1:]))
