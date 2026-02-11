from coreason_manifest.builder import NewGraphFlow, NewLinearFlow
from coreason_manifest.spec.core.nodes import InspectorNode
from coreason_manifest.utils.visualizer import to_mermaid


def test_inspector_lifecycle_graph() -> None:
    # 1. Use NewGraphFlow builder to construct a flow
    flow_builder = NewGraphFlow(name="inspector-test-graph", version="0.25")

    # 2. Add an InspectorNode using .add_inspector()
    flow_builder.add_inspector(
        node_id="inspector-1",
        target="result.score",
        criteria="Score must be > 0.8",
        output="verification_result",
        pass_threshold=0.8,
    )

    # 3. Build the flow
    flow = flow_builder.build()

    # 4. Assertions
    # Verify the node exists in flow.graph.nodes
    assert "inspector-1" in flow.graph.nodes

    node = flow.graph.nodes["inspector-1"]

    # Verify it is an instance of InspectorNode
    assert isinstance(node, InspectorNode)

    # Verify pass_threshold is set correctly
    assert node.pass_threshold == 0.8
    assert node.target_variable == "result.score"
    assert node.criteria == "Score must be > 0.8"

    # Run to_mermaid(flow) and verify the classDef inspector is present
    mermaid_code = to_mermaid(flow)

    # Check for class definition
    assert "classDef inspector fill:#e8daef,stroke:#8e44ad,stroke-width:2px;" in mermaid_code

    # Check for node rendering (expecting mermaid hexagon syntax {{ }})
    # Note: _safe_id replaces '-' with '_'
    # f'{safe_id}{{{{"{label_id}<br/>(Inspector)"}}}}'
    expected_node_str = 'inspector_1{{"inspector-1<br/>(Inspector)"}}'
    assert expected_node_str in mermaid_code

    # Check for class application
    assert "class inspector_1 inspector;" in mermaid_code


def test_inspector_lifecycle_linear() -> None:
    # 1. Use NewLinearFlow builder to construct a flow
    flow_builder = NewLinearFlow(name="inspector-test-linear", version="0.25")

    # 2. Add an InspectorNode using .add_inspector()
    flow_builder.add_inspector(
        node_id="inspector-2",
        target="result.quality",
        criteria="Quality must be high",
        output="quality_check",
        pass_threshold=0.9,
    )

    # 3. Build the flow
    flow = flow_builder.build()

    # 4. Assertions
    # Verify the node exists in flow.sequence
    assert len(flow.sequence) == 1
    node = flow.sequence[0]

    # Verify it is an instance of InspectorNode
    assert isinstance(node, InspectorNode)
    assert node.id == "inspector-2"

    # Verify properties
    assert node.pass_threshold == 0.9
    assert node.target_variable == "result.quality"

    # Run to_mermaid(flow) to verify visualization for linear flow
    mermaid_code = to_mermaid(flow)
    assert "classDef inspector fill:#e8daef,stroke:#8e44ad,stroke-width:2px;" in mermaid_code
    expected_node_str = 'inspector_2{{"inspector-2<br/>(Inspector)"}}'
    assert expected_node_str in mermaid_code
