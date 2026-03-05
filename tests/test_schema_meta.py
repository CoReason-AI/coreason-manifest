import json
from pathlib import Path

import jsonschema  # type: ignore[import-untyped]


def test_schema_valid() -> None:
    schema_path = Path("coreason_ontology.schema.json")
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.Draft202012Validator.check_schema(schema)
