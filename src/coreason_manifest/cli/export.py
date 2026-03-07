# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import importlib
import json
import sys
from pathlib import Path


def main() -> None:
    try:
        manifest = importlib.import_module("coreason_manifest")
    except ImportError as e:
        print(f"Failed to import coreason_manifest: {e}")
        sys.exit(1)

    models_to_export = []

    # We should also import CoreasonBaseModel to check isinstance/issubclass
    # Import all domains dynamically to collect schemas
    from pydantic import TypeAdapter

    from coreason_manifest.core import CoreasonBaseModel

    # Dynamically discover all schemas from the single source of truth (the root __all__)
    for name in set(getattr(manifest, "__all__", [])):
        obj = getattr(manifest, name)

        # Skip the base class
        if obj is CoreasonBaseModel:
            continue

        try:
            TypeAdapter(obj)

            models_to_export.append((obj, "validation"))
        except Exception:  # noqa: S112
            continue

    # Mathematical deterministic sort based on class name to guarantee stable Merkle hashing
    # For TypeAlias or Annotated, we can fallback to the string name of the type or alias
    models_to_export = sorted(models_to_export, key=lambda x: getattr(x[0], "__name__", str(x[0])))

    if not models_to_export:
        print("No models found to export.")
        sys.exit(0)

    definitions = {}
    any_ofs = []

    for obj, _ in models_to_export:
        adapter = TypeAdapter(obj)
        # Use a single schema generator instance to ensure shared $defs resolution
        schema = adapter.json_schema(by_alias=True, ref_template="#/$defs/{model}")

        # Name resolution for discriminated unions / TypeAliases
        name = getattr(obj, "__name__", str(obj))

        if "$defs" in schema:
            definitions.update(schema.pop("$defs"))

        definitions[name] = schema
        any_ofs.append({"$ref": f"#/$defs/{name}"})

    top_level_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Coreason Ontology",
        "description": "Unified JSON Schema for the Coreason Manifest",
        "$defs": definitions,
        "anyOf": any_ofs
    }

    schema_path = Path("coreason_ontology.schema.json")
    with schema_path.open("w", encoding="utf-8") as f:
        json.dump(top_level_schema, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Successfully exported {len(models_to_export)} models to {schema_path}")


if __name__ == "__main__":
    main()
