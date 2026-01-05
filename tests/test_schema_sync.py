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

    # Check definitions if any (nested models often go here in Pydantic v2)
    # Pydantic v2 puts nested models in $defs. The manual schema might use properties directly or definitions.
    # If the manual schema is fully expanded (no $ref), validation might be tricky.
    # Let's see what the structure looks like first by running this.
