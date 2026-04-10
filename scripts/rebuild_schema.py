# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import json
import sys
from pathlib import Path

# Configure Python path to allow importing coreason_manifest
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coreason_manifest.utils.algebra import get_ontology_schema


def main() -> None:
    schema = get_ontology_schema()
    out_path = Path(__file__).parent.parent / "coreason_ontology.schema.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Successfully rebuilt schema at {out_path}")


if __name__ == "__main__":
    main()
