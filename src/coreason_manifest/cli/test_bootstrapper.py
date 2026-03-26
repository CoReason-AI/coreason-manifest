import re
from pathlib import Path


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def generate_test(name: str) -> None:
    snake_case_name = camel_to_snake(name)
    test_file_path = Path(f"tests/fuzzing/test_mcp_{snake_case_name}.py")

    test_file_path.parent.mkdir(parents=True, exist_ok=True)

    test_content = f"""import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis_jsonschema import from_schema


def get_target_schema() -> dict:
    from coreason_manifest.spec.ontology import {name}
    return {name}.model_json_schema()


@given(from_schema(get_target_schema()))
def test_mcp_{snake_case_name}_fuzzing(instance):
    from coreason_manifest.spec.ontology import {name}
    obj = {name}.model_validate(instance)
    assert obj is not None
"""
    test_file_path.write_text(test_content, encoding="utf-8")
    print(f"Successfully bootstrapped test file at {test_file_path}")
