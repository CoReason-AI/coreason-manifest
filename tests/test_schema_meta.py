import json
import jsonschema  # type: ignore[import-untyped]
from pathlib import Path

def test_schema_validity() -> None:
    schema_path = Path("coreason_ontology.schema.json")
    assert schema_path.exists(), "Schema file not found"

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.Draft202012Validator.check_schema(schema)
