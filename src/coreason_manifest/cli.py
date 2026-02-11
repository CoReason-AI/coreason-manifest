# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import argparse
import sys


def main() -> int:
    """Entry point for the coreason CLI."""
    parser = argparse.ArgumentParser(description="CoReason Manifest CLI")
    parser.add_argument("--version", action="version", version="%(prog)s 0.23.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a manifest file")
    validate_parser.add_argument("file", help="Path to the manifest file")

    args = parser.parse_args()

    if args.command == "validate":
        print(f"Validation of {args.file} is not yet implemented in the new Core Kernel.")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
