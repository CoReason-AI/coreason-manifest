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
from importlib.metadata import PackageNotFoundError, version

from coreason_manifest.utils.loader import load_flow_from_file
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.utils.visualizer import to_mermaid


def main() -> int:
    """Entry point for the coreason CLI."""
    try:
        pkg_version = version("coreason_manifest")
    except PackageNotFoundError:
        pkg_version = "unknown"

    parser = argparse.ArgumentParser(prog="coreason", description="CoReason Manifest CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {pkg_version}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a manifest file")
    validate_parser.add_argument("file", help="Path to the manifest file")

    # Visualize command
    visualize_parser = subparsers.add_parser("visualize", help="Generate Mermaid diagram from manifest")
    visualize_parser.add_argument("file", help="Path to the manifest file")

    args = parser.parse_args()

    if args.command == "validate":
        return _handle_validate(args.file)

    if args.command == "visualize":
        return _handle_visualize(args.file)

    parser.print_help()
    return 0


def _handle_validate(file_path: str) -> int:
    try:
        flow = load_flow_from_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error loading file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected Error: {e}", file=sys.stderr)
        return 1

    errors = validate_flow(flow)

    if not errors:
        print("✅ Flow is valid.")
        return 0

    print("❌ Validation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    return 1


def _handle_visualize(file_path: str) -> int:
    try:
        flow = load_flow_from_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error loading file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected Error: {e}", file=sys.stderr)
        return 1

    # Optional: Warn if invalid, but proceed
    errors = validate_flow(flow)
    if errors:
        print("⚠️ Warning: Flow has validation errors:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)

    diagram = to_mermaid(flow)
    print(diagram)
    return 0


if __name__ == "__main__":
    sys.exit(main())
