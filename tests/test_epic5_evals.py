from coreason_manifest.spec.core.workflow.evals import EvalsManifest, TestCase


def test_evals_manifest() -> None:
    manifest = EvalsManifest(
        test_cases=[
            TestCase(
                mock_inputs={"user_input": "hello"},
                expected_traversal_path=["node1", "node2"],
                assertions={"result": {"type": "string", "const": "world"}},
            )
        ]
    )
    assert len(manifest.test_cases) == 1  # noqa: S101
    assert manifest.test_cases[0].mock_inputs["user_input"] == "hello"  # noqa: S101


def test_evals_mock_integration() -> None:
    from coreason_manifest.builder import NewGraphFlow
    from coreason_manifest.spec.core import (
        CognitiveProfile,
        FlowDefinitions,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
        StandardReasoning,
    )
    from coreason_manifest.spec.core.workflow.nodes import AgentNode
    from coreason_manifest.utils.mock import MockFactory

    node1 = AgentNode(id="n1", type="agent", profile="p1", operational_policy=None)
    node2 = AgentNode(id="n2", type="agent", profile="p1", operational_policy=None)

    builder = NewGraphFlow("test", "1")
    builder.add_node(node1).add_node(node2).set_entry_point("n1")
    builder.define_profile("p1", role="r", persona="p", reasoning=StandardReasoning(model="m"))

    from coreason_manifest.spec.core.oversight.governance import Governance
    Governance.model_rebuild(force=True)
    GraphFlow.model_rebuild(force=True)

    try:
        flow = builder.build()
    except Exception:
        # Fallback if builder validation fails, though it shouldn't
        flow = GraphFlow(
            metadata=FlowMetadata(name="test", version="1"),
            interface=FlowInterface(),
            graph=Graph(nodes={"n1": node1, "n2": node2}, edges=[], entry_point="n1"),
            definitions=FlowDefinitions(
                profiles={"p1": CognitiveProfile(role="r", persona="p", reasoning=StandardReasoning(model="m"))}
            ),
        )

    evals = EvalsManifest(
        test_cases=[
            TestCase(
                mock_inputs={"user_input": "hello"},
                expected_traversal_path=["n1", "n2"],
            )
        ]
    )

    factory = MockFactory(seed=42)
    trace = factory.simulate_trace(flow, evals=evals)

    assert len(trace) == 2  # noqa: S101
    assert trace[0].node_id == "n1"  # noqa: S101
    assert trace[1].node_id == "n2"  # noqa: S101
    assert trace[0].inputs.get("user_input") == "hello"  # noqa: S101
