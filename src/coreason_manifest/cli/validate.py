"""
AGENT INSTRUCTION: This module enforces the mathematical boundaries of the Hollow Data Plane for edge workers.
It MUST remain pure, stateless, and entirely devoid of dynamic reflection.
"""
import argparse
import sys
from typing import Final

from pydantic import BaseModel, ValidationError

from coreason_manifest.state.cognition import CognitiveStateProfile  # Representative schema
from coreason_manifest.state.differentials import StatePatch  # Representative schema

# Statically bound God-Context imports
from coreason_manifest.state.vision import DocumentLayoutAnalysis

# Immutable AOT Schema Registry
SCHEMA_REGISTRY: Final[dict[str, type[BaseModel]]] = {
    "step8_vision": DocumentLayoutAnalysis,
    "delta_update": StatePatch,
    "cognitive_sync": CognitiveStateProfile,
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

    try:
        with open(args.payload_path, "rb") as f:
            payload_bytes = f.read()
    except OSError as e:
        sys.stderr.write(f"FATAL: IO Error reading payload: {e}\n")
        sys.exit(1)

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
