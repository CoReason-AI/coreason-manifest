
import pytest
import math
from typing import Any
from coreason_manifest.spec.core.flow import (
    DataSchema,
    Edge,
    VariableDef,
    GraphFlow,
    FlowMetadata,
    FlowInterface,
    Blackboard,
    Graph,
    FlowDefinitions,
)
from coreason_manifest.spec.core.nodes import SwarmNode, AgentNode, CognitiveProfile
from coreason_manifest.spec.core.constants import NodeCapability
from coreason_manifest.spec.interop.antibody import AntibodyBase, DataAnomaly
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.spec.interop.compliance import ErrorCatalog
from coreason_manifest.utils.gatekeeper import validate_policy, _is_guarded
from coreason_manifest.spec.core.engines import ComputerUseReasoning

# --- Flow Compatibility Tests ---

def test_flow_backwards_compatibility():
    # DataSchema: schema -> json_schema
    ds = DataSchema(**{"schema": {"type": "string"}})
    assert ds.json_schema == {"type": "string"}

    # Edge: source/target -> from_node/to_node
    edge = Edge(**{"source": "a", "target": "b"})
    assert edge.from_node == "a"
    assert edge.to_node == "b"

    # VariableDef: name -> id
    var = VariableDef(**{"name": "v1", "type": "string"})
    assert var.id == "v1"

def test_swarm_variable_validation():
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
        output_variable="out_var"
    )

    # We need a valid GraphFlow structure
    # Use model_construct to avoid validation during creation of sub-parts if possible,
    # but here we want to trigger the GraphFlow validator.

    with pytest.raises(ManifestError, match="references missing workload variable"):
        GraphFlow(
            metadata=FlowMetadata(name="test", version="1.0"),
            interface=FlowInterface(),
            blackboard=Blackboard(variables={"existing_var": []}),
            graph=Graph(nodes={"swarm1": swarm_node}, edges=[]),
            definitions=FlowDefinitions(profiles={})
        )

# --- Antibody Tests ---

class MyModel(AntibodyBase):
    val: Any

def test_antibody_nan_inf():
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

def test_antibody_list_nan():
    # Test List with NaN
    data_list = {"val": [1.0, float("nan")]}
    model_list = MyModel(**data_list)
    assert isinstance(model_list.val, list)
    assert model_list.val[0] == 1.0
    assert isinstance(model_list.val[1], dict)
    assert model_list.val[1]["code"] == "CRSN-ANTIBODY-FLOAT"

def test_antibody_unserializable():
    # Test Unserializable (set)
    data_set = {"val": {1, 2}}
    # set is not in VALID_PRIMITIVES and not dict/list
    model_set = MyModel(**data_set)
    assert isinstance(model_set.val, dict)
    assert model_set.val["code"] == "CRSN-ANTIBODY-UNSERIALIZABLE"

def test_antibody_nested_list():
    # Test List containing Dict (recursive scan)
    data_nested = {"val": [{"inner": float("nan")}]}
    model_nested = MyModel(**data_nested)
    assert isinstance(model_nested.val, list)
    assert isinstance(model_nested.val[0], dict)
    assert isinstance(model_nested.val[0]["inner"], dict)
    assert model_nested.val[0]["inner"]["code"] == "CRSN-ANTIBODY-FLOAT"

def test_swarm_variable_valid():
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
        output_variable="out_var"
    )

    flow = GraphFlow.model_construct(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        blackboard=Blackboard(variables={"existing_var": []}),
        graph=Graph(nodes={"swarm1": swarm_node}, edges=[]),
        definitions=FlowDefinitions(profiles={})
    )

    # Should NOT raise
    validated = flow.validate_swarm_variables()
    assert validated is flow

def test_validate_swarm_variables_no_blackboard():
    # Construct GraphFlow without blackboard (simulating None)
    # Using model_construct allows bypassing defaults/validation
    flow = GraphFlow.model_construct(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        blackboard=None, # Explicitly None
        graph=Graph(nodes={}, edges=[]),
        definitions=FlowDefinitions(profiles={})
    )

    # Should return self immediately (line 162)
    validated = flow.validate_swarm_variables()
    assert validated is flow
    assert flow.blackboard is None

# --- Gatekeeper Tests ---

def test_gatekeeper_no_entry_point():
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
            entry_point=None # Explicitly None
        ),
        definitions=FlowDefinitions(profiles={}) # To avoid profile lookup issues
    )

    if not flow.definitions:
        flow.definitions = FlowDefinitions()

    reports = validate_policy(flow)

    # Should report unsafe because it's not guarded (and not reachable)
    # The error ERR_SEC_UNGUARDED_CRITICAL_003 should be present
    unguarded_errors = [r for r in reports if r.code == ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003]
    assert len(unguarded_errors) > 0

def test_gatekeeper_bfs_traversal():
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
            nodes={"A": node_a, "B": node_b},
            edges=[Edge(from_node="A", to_node="B")],
            entry_point="A"
        ),
        definitions=FlowDefinitions(profiles={})
    )

    reports = validate_policy(flow)

    # Should report unsafe because B is not guarded by HumanNode
    unguarded_errors = [r for r in reports if r.code == ErrorCatalog.ERR_SEC_UNGUARDED_CRITICAL_003]
    assert len(unguarded_errors) > 0

def test_flow_nodes_iter_list_coverage() -> None:
    # Cover flow.py line 162 else branch
    # We need to construct GraphFlow such that graph.nodes is a list
    # This requires model_construct because Pydantic expects dict

    agent = AgentNode(id="a1", type="agent", profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None), tools=[], metadata={}, resilience=None)

    # Manually call the validator
    swarm = SwarmNode(
        id="s1", type="swarm", worker_profile="p1", workload_variable="v",
        distribution_strategy="sharded", max_concurrency=1, reducer_function="concat",
        output_variable="out", metadata={}, resilience=None
    )

    # Construct with list nodes in graph (bypassing validation type check)
    # We use model_construct for Graph to inject list
    graph_with_list = Graph.model_construct(
        nodes=[agent, swarm],
        edges=[],
        entry_point="a1"
    )

    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        blackboard=Blackboard(variables={"v": {"type": "list", "id": "v"}}),
        graph=graph_with_list
    )

    # Should pass (variable 'v' is in blackboard) and iterate over list
    flow.validate_swarm_variables()
