# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from pathlib import Path
from typing import Type

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.recipes import RecipeManifest
from pydantic import BaseModel


def verify_schema(model: Type[BaseModel], schema_path: Path) -> None:
    """Helper to verify schema synchronization."""
    # Generate schema from Pydantic
    generated_schema = model.model_json_schema()

    # Load stored schema
    with open(schema_path, "r", encoding="utf-8") as f:
        stored_schema = json.load(f)

    # Check strict equality of properties and required fields
    assert stored_schema.get("properties") == generated_schema.get("properties"), "Schema properties do not match model"
    assert set(stored_schema.get("required", [])) == set(
        generated_schema.get("required", [])
    ), "Required fields do not match model"

    # Check definitions ($defs)
    stored_defs = stored_schema.get("$defs", {})
    generated_defs = generated_schema.get("$defs", {})

    # Compare keys
    assert set(stored_defs.keys()) == set(generated_defs.keys()), "Schema definitions keys do not match"

    # Compare content of each definition
    for key in stored_defs:
        assert stored_defs[key] == generated_defs[key], f"Definition '{key}' does not match model"


def test_agent_schema_sync() -> None:
    """
    Verify that the stored JSON schema matches the Pydantic model's generated schema.
    This ensures that the Pydantic model is the single source of truth.
    """
    verify_schema(AgentDefinition, Path("src/coreason_manifest/schemas/agent.schema.json"))


def test_recipe_schema_sync() -> None:
    """Verify RecipeManifest schema."""
    verify_schema(RecipeManifest, Path("src/coreason_manifest/schemas/recipe.schema.json"))
