# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""AGENT INSTRUCTION: Regenerates the coreason_ontology.schema.json from the live Pydantic models."""

import json
from pathlib import Path

from coreason_manifest.utils.algebra import get_ontology_schema


def main() -> None:
    schema = get_ontology_schema()
    output_path = Path(__file__).resolve().parent.parent / "coreason_ontology.schema.json"
    with open(output_path, "w", newline="\n") as f:
        json.dump(schema, f, indent=2, sort_keys=True)
        f.write("\n")
    num_defs = len(schema.get("$defs", {}))
    print(f"Schema regenerated successfully: {output_path}")
    print(f"Total definitions: {num_defs}")


if __name__ == "__main__":
    main()
