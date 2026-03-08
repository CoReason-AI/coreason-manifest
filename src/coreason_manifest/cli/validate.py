# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This is a pure, side-effect-free POSIX CLI script for structural linting.
It strictly adheres to the Hollow Data Plane constraint.
NO runtime logging, NO network sockets, NO async loops.
"""

import argparse
import sys
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

import coreason_manifest
from coreason_manifest.core.base import CoreasonBaseModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Structural Linter for CoReason Manifest.")
    parser.add_argument("--schema", required=True, help="The exact name of the Pydantic schema class.")
    parser.add_argument("payload_path", type=Path, help="Path to the JSON payload file.")

    args = parser.parse_args()

    schema_class = getattr(coreason_manifest, args.schema, None)
    if schema_class is None or not (isinstance(schema_class, type) and issubclass(schema_class, CoreasonBaseModel)):
        sys.stderr.write(
            f"Error: Schema '{args.schema}' not found in coreason_manifest or is not a CoreasonBaseModel.\n"
        )
        sys.exit(1)

    if not args.payload_path.exists():
        sys.stderr.write(f"Error: Payload file '{args.payload_path}' does not exist.\n")
        sys.exit(1)

    raw_bytes = args.payload_path.read_bytes()

    try:
        TypeAdapter(schema_class).validate_json(raw_bytes)
    except (ValidationError, ValueError) as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
