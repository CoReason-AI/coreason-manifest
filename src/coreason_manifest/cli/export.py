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

from pydantic.json_schema import models_json_schema


def main() -> None:
    try:
        manifest = importlib.import_module("coreason_manifest")
    except ImportError as e:
        print(f"Failed to import coreason_manifest: {e}")
        sys.exit(1)

    models_to_export = []

    # We should also import CoreasonBaseModel to check isinstance/issubclass
    from coreason_manifest.core import CoreasonBaseModel

    # Import all domains dynamically to collect schemas
    domains = [
        "coreason_manifest.core",
        "coreason_manifest.oversight",
        "coreason_manifest.state",
        "coreason_manifest.testing",
        "coreason_manifest.tooling",
        "coreason_manifest.workflow",
        "coreason_manifest.telemetry",
        "coreason_manifest.compute",
    ]

    for domain in domains:
        try:
            mod = importlib.import_module(domain)
            for name in getattr(mod, "__all__", []):
                obj = getattr(mod, name)
                if isinstance(obj, type) and issubclass(obj, CoreasonBaseModel) and obj is not CoreasonBaseModel:
                    models_to_export.append((obj, "validation"))
        except ImportError:
            pass

    # Include any root schemas just in case
    for name in getattr(manifest, "__all__", []):
        obj = getattr(manifest, name)
        if isinstance(obj, type) and issubclass(obj, CoreasonBaseModel) and obj is not CoreasonBaseModel:
            models_to_export.append((obj, "validation"))

    # Remove duplicates
    unique_models = {}
    for obj, type_ in models_to_export:
        unique_models[obj] = (obj, type_)
    models_to_export = list(unique_models.values())

    if not models_to_export:
        print("No models found to export.")
        sys.exit(0)

    _, top_level_schema = models_json_schema(
        models_to_export,  # type: ignore
        title="Coreason Ontology",
        description="Unified JSON Schema for the Coreason Manifest",
    )

    schema_path = Path("coreason_ontology.schema.json")
    with schema_path.open("w", encoding="utf-8") as f:
        json.dump(top_level_schema, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Successfully exported {len(models_to_export)} models to {schema_path}")


if __name__ == "__main__":
    main()
