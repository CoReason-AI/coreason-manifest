import pytest
from pydantic import ValidationError
from coreason_manifest.spec.core.flow import FlowInterface, DataSchema
from coreason_manifest.builder import NewGraphFlow

def test_flow_interface_schema():
    input_schema = DataSchema(fields={"user_query": "str"}, required=["user_query"])
    output_schema = DataSchema(fields={"response": "str"}, required=["response"])

    interface = FlowInterface(inputs=input_schema, outputs=output_schema)
    assert interface.inputs.fields["user_query"] == "str"
    assert "user_query" in interface.inputs.required

def test_flow_interface_validation_error():
    with pytest.raises(ValidationError):
        FlowInterface(inputs={"bad": "dict"}, outputs={})

def test_builder_interface_construction():
    builder = NewGraphFlow("test", "1.0", "desc")
    builder.set_interface(
        inputs={"query": "str"},
        outputs={"answer": "str"}
    )
    # NewGraphFlow.build() validates the flow.
    # It requires at least one node if it checks for empty graph?
    # validator.py: "GraphFlow Error: Graph must contain at least one node."
    # So we need to add a node.

    from coreason_manifest.spec.core.nodes import PlaceholderNode
    node = PlaceholderNode(
        id="start",
        metadata={},
        supervision=None,
        type="placeholder",
        required_capabilities=[]
    )
    builder.add_node(node)

    flow = builder.build()

    assert isinstance(flow.interface.inputs, DataSchema)
    assert flow.interface.inputs.fields["query"] == "str"
    assert "query" in flow.interface.inputs.required
    assert flow.interface.outputs.fields["answer"] == "str"
