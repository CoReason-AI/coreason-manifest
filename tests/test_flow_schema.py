import pytest
from pydantic import ValidationError

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.flow import DataSchema, FlowInterface


def test_flow_interface_schema() -> None:
    input_schema = DataSchema(schema={"type": "object", "properties": {"user_query": {"type": "string"}}})
    output_schema = DataSchema(schema={"type": "object", "properties": {"response": {"type": "string"}}})

    interface = FlowInterface(inputs=input_schema, outputs=output_schema)
    assert isinstance(interface.inputs.schema, dict)
    assert interface.inputs.schema["properties"]["user_query"]["type"] == "string"


def test_flow_interface_validation_error() -> None:
    with pytest.raises(ValidationError):
        FlowInterface(
            inputs={"json_schema": "invalid-type"},  # type: ignore[arg-type]
            outputs=DataSchema(schema={}),
        )


def test_builder_interface_construction() -> None:
    builder = NewGraphFlow("test", "1.0.0", "desc")
    # Builder now accepts raw dicts for schema
    input_s = {"type": "object", "properties": {"query": {"type": "string"}}}
    output_s = {"type": "object", "properties": {"answer": {"type": "string"}}}
    builder.set_interface(inputs=input_s, outputs=output_s)

    from coreason_manifest.spec.core.nodes import PlaceholderNode

    node = PlaceholderNode(id="start", metadata={}, type="placeholder", required_capabilities=[])
    builder.add_node(node)

    flow = builder.build()

    assert isinstance(flow.interface.inputs, DataSchema)
    assert isinstance(flow.interface.inputs.schema, dict)
    assert flow.interface.inputs.schema["properties"]["query"]["type"] == "string"
    assert isinstance(flow.interface.outputs.schema, dict)
    assert flow.interface.outputs.schema["properties"]["answer"]["type"] == "string"
