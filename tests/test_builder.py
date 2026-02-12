import pytest

from coreason_manifest.builder import NewGraphFlow, NewLinearFlow
from coreason_manifest.spec.core.flow import VariableDef
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import Placeholder
from coreason_manifest.spec.core.tools import ToolPack


def test_linear_builder() -> None:
    builder = NewLinearFlow("MyLinear", version="1.0", description="Desc")
    builder.add_step(
        Placeholder(id="step1", type="placeholder", metadata={}, supervision=None, required_capabilities=[])
    )
    builder.add_step(
        Placeholder(id="step2", type="placeholder", metadata={}, supervision=None, required_capabilities=[])
    )

    tp = ToolPack(kind="ToolPack", namespace="test", tools=["t1"], dependencies=[], env_vars=[])
    builder.add_tool_pack(tp)

    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    flow = builder.build()

    assert flow.kind == "LinearFlow"
    assert flow.metadata.name == "MyLinear"
    assert len(flow.sequence) == 2
    assert flow.definitions is not None
    assert len(flow.definitions.tool_packs) == 1
    assert flow.governance is not None
    assert flow.governance.rate_limit_rpm == 10


def test_graph_builder() -> None:
    builder = NewGraphFlow("MyGraph", version="1.0", description="Desc")
    builder.add_node(Placeholder(id="n1", type="placeholder", metadata={}, supervision=None, required_capabilities=[]))
    builder.add_node(Placeholder(id="n2", type="placeholder", metadata={}, supervision=None, required_capabilities=[]))
    builder.connect("n1", "n2", condition="ok")

    tp = ToolPack(kind="ToolPack", namespace="test", tools=["t1"], dependencies=[], env_vars=[])
    builder.add_tool_pack(tp)

    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    # Test set_interface and set_blackboard
    builder.set_interface(inputs={"in": "str"}, outputs={"out": "int"})
    builder.set_blackboard(variables={"var1": VariableDef(type="string", description="test var")}, persistence=True)

    flow = builder.build()

    assert flow.kind == "GraphFlow"
    assert flow.metadata.name == "MyGraph"
    assert len(flow.graph.nodes) == 2
    assert len(flow.graph.edges) == 1
    assert flow.graph.edges[0].source == "n1"
    assert flow.graph.edges[0].target == "n2"
    assert flow.graph.edges[0].condition == "ok"
    assert flow.definitions is not None
    assert len(flow.definitions.tool_packs) == 1
    assert flow.governance is not None
    assert flow.governance.rate_limit_rpm == 10

    # Assert new features
    assert flow.interface.inputs == {"in": "str"}
    assert flow.interface.outputs == {"out": "int"}
    assert flow.blackboard is not None
    assert flow.blackboard.persistence is True
    assert "var1" in flow.blackboard.variables
    assert flow.blackboard.variables["var1"].type == "string"


def test_linear_builder_invalid() -> None:
    # Empty sequence is invalid
    builder = NewLinearFlow("Invalid")
    with pytest.raises(ValueError, match="Validation failed"):
        builder.build()


def test_graph_builder_invalid() -> None:
    # Empty graph is invalid
    builder = NewGraphFlow("Invalid")
    with pytest.raises(ValueError, match="Validation failed"):
        builder.build()
