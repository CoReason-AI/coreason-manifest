# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import json
import sys
import typing
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

import coreason_manifest
from coreason_manifest.spec.ontology import CoreasonBaseModel


def main() -> None:
    models_to_export: list[type[CoreasonBaseModel]] = []

    for name in sorted(set(coreason_manifest.__all__)):
        obj = getattr(coreason_manifest, name, None)
        # Strictly filter for BaseModel classes only to avoid crashing models_json_schema
        if isinstance(obj, type) and issubclass(obj, CoreasonBaseModel) and obj is not CoreasonBaseModel:
            models_to_export.append(obj)

    if not models_to_export:
        print("No models found to export.")
        sys.exit(0)

    pydantic_models = cast(
        "Sequence[tuple[type[BaseModel], typing.Literal['validation']]]",
        [(m, "validation") for m in models_to_export],
    )

    _, top_level_schema = models_json_schema(
        pydantic_models,
        title="CoReason Shared Kernel Ontology",
        description="Unified JSON Schema for the Coreason Manifest",
    )

    schema_path = Path("coreason_ontology.schema.json")
    with schema_path.open("w", encoding="utf-8") as f:
        json.dump(top_level_schema, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Successfully exported {len(models_to_export)} models to {schema_path}")


if __name__ == "__main__":
    main()
