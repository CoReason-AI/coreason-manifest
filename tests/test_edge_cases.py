from typing import Any

import pytest

from coreason_manifest.spec.core.engines import ComputerUseReasoning
from coreason_manifest.spec.core.flow import (
    Blackboard,
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    VariableDef,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, SwarmNode
from coreason_manifest.spec.interop.antibody import AntibodyBase
from coreason_manifest.spec.interop.compliance import ErrorCatalog
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.validator import validate_flow

# --- Flow Compatibility Tests ---


def test_flow_backwards_compatibility() -> None:
    # DataSchema: schema -> json_schema
    ds = DataSchema(json_schema={"type": "string"})
    assert ds.json_schema == {"type": "string"}

    ds_compat = DataSchema(schema={"type": "string"})  # type: ignore[call-arg]
    assert ds_compat.json_schema == {"type": "string"}

    # Edge: source/target -> from_node/to_node
    # Removed backward compatibility: source/target now raise ValidationError
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Edge(source="a", target="b")  # type: ignore[call-arg]

    # VariableDef: name -> id
    var = VariableDef(name="v1", type="string")  # type: ignore[call-arg]
    assert var.id == "v1"


def test_swarm_variable_validation() -> None:
    # Create a SwarmNode referencing a variable NOT in blackboard
    swarm_node = SwarmNode(
        id="swarm1",
        type="swarm",
        worker_profile="worker",
        workload_variable="missing_var",
        metadata={},
        distribution_strategy="sharded",
        max_concurrency=5,
        reducer_function="concat",
        output_variable="out_var",
    )

    flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        blackboard=Blackboard(variables={"existing_var": []}),
        graph=Graph(nodes={"swarm1": swarm_node}, edges=[]),
        definitions=FlowDefinitions(profiles={}),
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_MISSING_VAR" and e.details.get("variable") == "missing_var" for e in errors)


# --- Antibody Tests ---


class MyModel(AntibodyBase):
    val: Any


def test_antibody_nan_inf() -> None:
    # Test NaN
    data_nan = {"val": float("nan")}
    model_nan = MyModel(**data_nan)
    assert isinstance(model_nan.val, dict)
    assert model_nan.val["code"] == "CRSN-ANTIBODY-FLOAT"
    assert "nan" in model_nan.val["value_repr"].lower()

    # Test Inf
    data_inf = {"val": float("inf")}
    model_inf = MyModel(**data_inf)
    assert isinstance(model_inf.val, dict)
    assert model_inf.val["code"] == "CRSN-ANTIBODY-FLOAT"
    assert "inf" in model_inf.val["value_repr"]


def test_antibody_list_nan() -> None:
    # Test List with NaN
    data_list = {"val": [1.0, float("nan")]}
    model_list = MyModel(**data_list)
    assert isinstance(model_list.val, list)
    assert model_list.val[0] == 1.0
    assert isinstance(model_list.val[1], dict)
    assert model_list.val[1]["code"] == "CRSN-ANTIBODY-FLOAT"


def test_antibody_unserializable() -> None:
    # Test Unserializable (set)
    data_set = {"val": {1, 2}}
    # set is not in VALID_PRIMITIVES and not dict/list
    model_set = MyModel(**data_set)
    assert isinstance(model_set.val, dict)
    assert model_set.val["code"] == "CRSN-ANTIBODY-UNSERIALIZABLE"


def test_antibody_nested_list() -> None:
    # Test List containing Dict (recursive scan)
    data_nested = {"val": [{"inner": float("nan")}]}
    model_nested = MyModel(**data_nested)
    assert isinstance(model_nested.val, list)
    assert isinstance(model_nested.val[0], dict)
    assert isinstance(model_nested.val[0]["inner"], dict)
    assert model_nested.val[0]["inner"]["code"] == "CRSN-ANTIBODY-FLOAT"


def test_swarm_variable_valid() -> None:
    # Create a SwarmNode referencing a VALID variable
    swarm_node = SwarmNode(
        id="swarm1",
        type="swarm",
        worker_profile="worker",
        workload_variable="existing_var",
        metadata={},
        distribution_strategy="sharded",
        max_concurrency=5,
        reducer_function="concat",
        output_variable="out_var",
    )

    # Use VariableDef for blackboard variables
    flow = GraphFlow.model_construct(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        # Use VariableDef with explicit type
        blackboard=Blackboard(
            variables={"existing_var": VariableDef(type="list"), "out_var": VariableDef(type="list")}
        ),
        graph=Graph(nodes={"swarm1": swarm_node}, edges=[]),
        definitions=FlowDefinitions(profiles={}),
    )

    # Should NOT raise
    errors = validate_flow(flow)
    swarm_errors = [e for e in errors if e.code in ["ERR_CAP_MISSING_VAR", "ERR_CAP_TYPE_MISMATCH"]]
    assert not swarm_errors, f"Validation errors: {swarm_errors}"


def test_validate_swarm_variables_no_blackboard() -> None:
    # Construct GraphFlow without blackboard (simulating None)
    flow = GraphFlow.model_construct(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        blackboard=None,  # Explicitly None
        graph=Graph(nodes={}, edges=[]),
        definitions=FlowDefinitions(profiles={}),
    )

    errors = validate_flow(flow)
    assert flow.blackboard is None
    assert not any(e.code == "ERR_CAP_MISSING_VAR" for e in errors)


# --- Gatekeeper Tests ---


def test_gatekeeper_no_entry_point() -> None:
    """
    Test GraphFlow with entry_point=None containing an unsafe node.
    This triggers _is_guarded -> lines 368-369 (full_queue = []).
    """
    # Unsafe node
    unsafe_reasoning = ComputerUseReasoning(model="claude-3-5-sonnet")
    profile = CognitiveProfile(role="hacker", persona="unsafe", reasoning=unsafe_reasoning, fast_path=None)

    node = AgentNode(id="unsafe", type="agent", metadata={}, profile=profile, tools=[])

    flow = GraphFlow.model_construct(
        metadata=FlowMetadata(name="test", version="1.0"),
        graph=Graph.model_construct(
            nodes={"unsafe": node},
            edges=[],
            entry_point=None,  # Explicitly None
        ),
        definitions=FlowDefinitions(profiles={}),  # To avoid profile lookup issues
        interface=FlowInterface(),
    )

    reports = validate_policy(flow)

    # Should report unsafe because it's not guarded (and not reachable)
    unguarded_errors = [r for r in reports if r.code == ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003]
    assert len(unguarded_errors) > 0


def test_gatekeeper_bfs_traversal() -> None:
    """
    Test GraphFlow with A -> B (unsafe).
    Triggers _is_guarded -> BFS traversal -> lines 380-381.
    """
    unsafe_reasoning = ComputerUseReasoning(model="claude-3-5-sonnet")
    unsafe_profile = CognitiveProfile(role="hacker", persona="unsafe", reasoning=unsafe_reasoning, fast_path=None)
    safe_profile = CognitiveProfile(role="safe", persona="safe", reasoning=None, fast_path=None)

    node_a = AgentNode(id="A", type="agent", metadata={}, profile=safe_profile, tools=[])
    node_b = AgentNode(id="B", type="agent", metadata={}, profile=unsafe_profile, tools=[])

    flow = GraphFlow.model_construct(
        metadata=FlowMetadata(name="test", version="1.0"),
        graph=Graph.model_construct(
            nodes={"A": node_a, "B": node_b}, edges=[Edge(from_node="A", to_node="B")], entry_point="A"
        ),
        definitions=FlowDefinitions(profiles={}),
        interface=FlowInterface(),  # Added missing required field
    )

    reports = validate_policy(flow)

    # Should report unsafe because B is not guarded by HumanNode
    unguarded_errors = [r for r in reports if r.code == ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003]
    assert len(unguarded_errors) > 0
