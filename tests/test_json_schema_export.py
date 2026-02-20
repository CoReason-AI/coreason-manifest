import json

from coreason_manifest.spec.core.flow import Manifest


def test_json_schema_export() -> None:
    """
    Test that Manifest.export_json_schema() returns a valid JSON Schema dict.
    """
    schema_str = Manifest.export_json_schema()
    assert isinstance(schema_str, str)

    schema = json.loads(schema_str)

    assert isinstance(schema, dict)
    assert "$defs" in schema  # Definitions should be present for complex types

    defs = schema["$defs"]
    assert "LinearFlow" in defs
    assert "GraphFlow" in defs

    # Check LinearFlow sequence items
    linear_flow = defs["LinearFlow"]
    sequence_items = linear_flow["properties"]["sequence"]["items"]

    # It should reference AnyNode or be AnyNode
    if "$ref" in sequence_items:
        ref_name = sequence_items["$ref"].split("/")[-1]
        assert ref_name in defs
        node_schema = defs[ref_name]
    else:
        # If inlined (unlikely for complex type)
        node_schema = sequence_items

    # Check that the node schema is a discriminated union
    # Pydantic v2 uses 'anyOf' or 'oneOf' with 'discriminator'
    assert "anyOf" in node_schema or "oneOf" in node_schema

    # Check that custom descriptions are present (random check)
    assert "Unique identifier for the node." in schema_str
    assert "Description of what the flow does." in schema_str
