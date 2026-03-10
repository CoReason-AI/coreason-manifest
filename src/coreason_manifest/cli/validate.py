# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""
AGENT INSTRUCTION: This module enforces the mathematical boundaries of the Hollow Data Plane for edge workers.
It MUST remain pure, stateless, and entirely devoid of dynamic reflection.
"""

import argparse
import sys
from typing import Final

from pydantic import BaseModel, ValidationError

# Statically bound God-Context imports
from coreason_manifest.spec.ontology import (
    CognitiveStateProfile,  # Representative schema
    DocumentLayoutManifest,
    StateMutationIntent,  # Representative schema
    System2RemediationIntent,
)

# Immutable AOT Schema Registry
SCHEMA_REGISTRY: Final[dict[str, type[BaseModel]]] = {
    "step8_vision": DocumentLayoutManifest,
    "state_differential": StateMutationIntent,
    "cognitive_sync": CognitiveStateProfile,
    "system2_remediation": System2RemediationIntent,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Coreason Manifest Offline Schema Linter")
    parser.add_argument("--step", type=str, required=True, help="The static schema registry identifier.")
    parser.add_argument("payload_path", type=str, help="Path to the local JSON payload.")

    args = parser.parse_args()

    target_schema = SCHEMA_REGISTRY.get(args.step)
    if not target_schema:
        sys.stderr.write(f"FATAL: Unknown step '{args.step}'. Valid steps: {list(SCHEMA_REGISTRY.keys())}\n")
        sys.exit(1)
        return

    try:
        with open(args.payload_path, "rb") as f:
            payload_bytes = f.read()
    except OSError as e:
        sys.stderr.write(f"FATAL: IO Error reading payload: {e}\n")
        sys.exit(1)
        return

    try:
        # Pure functional evaluation
        target_schema.model_validate_json(payload_bytes)
        sys.exit(0)
    except ValidationError as e:
        # AST-Compliant Error Projection (RFC 6902 parsable)
        sys.stderr.write(e.json())
        sys.stderr.write("\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
