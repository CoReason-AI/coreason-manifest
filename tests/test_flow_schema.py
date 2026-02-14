import pytest
from pydantic import ValidationError

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.flow import DataSchema, FlowInterface


def test_flow_interface_schema() -> None:
    input_schema = DataSchema(json_schema={"type": "object", "properties": {"user_query": {"type": "string"}}})
    output_schema = DataSchema(json_schema={"type": "object", "properties": {"response": {"type": "string"}}})

    interface = FlowInterface(inputs=input_schema, outputs=output_schema)
    assert interface.inputs.json_schema["properties"]["user_query"]["type"] == "string"


def test_flow_interface_validation_error() -> None:
    with pytest.raises(ValidationError):
        FlowInterface(
            inputs={"bad": "dict"},  # type: ignore[arg-type]
            outputs=DataSchema(json_schema={}),
        )


def test_builder_interface_construction() -> None:
    builder = NewGraphFlow("test", "1.0", "desc")
    # Builder now accepts raw dicts for schema
    input_s = {"type": "object", "properties": {"query": {"type": "string"}}}
    output_s = {"type": "object", "properties": {"answer": {"type": "string"}}}
    builder.set_interface(inputs=input_s, outputs=output_s)

    from coreason_manifest.spec.core.nodes import PlaceholderNode

    node = PlaceholderNode(id="start", metadata={}, supervision=None, type="placeholder", required_capabilities=[])
    builder.add_node(node)

    flow = builder.build()

    assert isinstance(flow.interface.inputs, DataSchema)
    assert flow.interface.inputs.json_schema["properties"]["query"]["type"] == "string"
    assert flow.interface.outputs.json_schema["properties"]["answer"]["type"] == "string"
