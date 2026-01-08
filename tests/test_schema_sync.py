# Prosperity-3.0
import json
from pathlib import Path

from coreason_manifest.models import AgentDefinition


def test_schema_sync() -> None:
    """
    Verify that the stored JSON schema matches the Pydantic model's generated schema.
    This ensures that the Pydantic model is the single source of truth.
    """
    # Generate schema from Pydantic
    generated_schema = AgentDefinition.model_json_schema()

    # Load stored schema
    schema_path = Path("src/coreason_manifest/schemas/agent.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        stored_schema = json.load(f)

    # We need to normalize some fields that Pydantic might generate differently or that we manually added.
    # For example, $schema and $id might be custom in the stored file.

    # Check strict equality of properties and required fields
    assert stored_schema.get("properties") == generated_schema.get("properties"), "Schema properties do not match model"
    assert set(stored_schema.get("required", [])) == set(generated_schema.get("required", [])), (
        "Required fields do not match model"
    )

    # Check definitions ($defs)
    # Both stored and generated schema use $defs for nested models
    stored_defs = stored_schema.get("$defs", {})
    generated_defs = generated_schema.get("$defs", {})

    # Compare keys
    assert set(stored_defs.keys()) == set(generated_defs.keys()), "Schema definitions keys do not match"

    # Compare content of each definition
    for key in stored_defs:
        assert stored_defs[key] == generated_defs[key], f"Definition '{key}' does not match model"
