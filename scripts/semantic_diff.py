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
import subprocess
import sys
from pathlib import Path


def get_head_schema() -> dict:
    try:
        output = subprocess.check_output(
            ["git", "show", "HEAD~1:coreason_ontology.schema.json"],  # noqa: S607
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return json.loads(output)
    except subprocess.CalledProcessError:
        # File might not exist in HEAD~1
        return {}


def get_current_schema() -> dict:
    path = Path("coreason_ontology.schema.json")
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_for_breaking_changes(old_schema: dict, new_schema: dict) -> list[str]:
    old_defs = old_schema.get("$defs", {})
    new_defs = new_schema.get("$defs", {})

    breaking_changes = []

    for name, old_def in old_defs.items():
        if name not in new_defs:
            continue

        new_def = new_defs[name]

        # Contravariance check on inputs
        # (Assuming 'properties' generally represent inputs/attributes, if a new property becomes 'required')
        old_required = set(old_def.get("required", []))
        new_required = set(new_def.get("required", []))

        added_required = new_required - old_required
        if added_required:
            breaking_changes.append(f"[{name}] Contravariance Violation: added required properties: {added_required}")

        # Covariance check:
        # Check if type changed
        old_props = old_def.get("properties", {})
        new_props = new_def.get("properties", {})

        for prop_name, old_prop in old_props.items():
            if prop_name in new_props:
                new_prop = new_props[prop_name]
                if old_prop.get("type") != new_prop.get("type"):
                    breaking_changes.append(
                        f"[{name}.{prop_name}] Covariance Violation: type changed from {old_prop.get('type')} to {new_prop.get('type')}"
                    )

    return breaking_changes


def main() -> None:
    old_schema = get_head_schema()
    new_schema = get_current_schema()

    if not old_schema or not new_schema:
        print("Could not load schemas for comparison.")
        sys.exit(0)

    breaking_changes = check_for_breaking_changes(old_schema, new_schema)

    if breaking_changes:
        print("Blast Radius Warning: Topological breakages detected.")
        for change in breaking_changes:
            print(f" - {change}")
        sys.exit(1)

    print("No topological breakages detected.")


if __name__ == "__main__":
    main()
