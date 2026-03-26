import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis_jsonschema import from_schema


def get_target_schema() -> dict:
    from coreason_manifest.spec.ontology import VectorSearch
    return VectorSearch.model_json_schema()


@given(from_schema(get_target_schema()))
def test_mcp_vector_search_fuzzing(instance):
    from coreason_manifest.spec.ontology import VectorSearch
    obj = VectorSearch.model_validate(instance)
    assert obj is not None
