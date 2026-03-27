from typing import Any

from hypothesis import given
from hypothesis_jsonschema import from_schema


def get_target_schema() -> dict[str, Any]:
    from coreason_manifest.spec.ontology import TestCapability

    return TestCapability.model_json_schema()


@given(from_schema(get_target_schema()))
def test_mcp_test_capability_fuzzing(instance: dict[str, Any]) -> None:
    from coreason_manifest.spec.ontology import TestCapability

    obj = TestCapability.model_validate(instance)
    assert obj is not None
