# tests/test_governance_fixes.py

import pytest
from pydantic import BaseModel, ValidationError

from coreason_manifest.spec.core.engines import CodeExecutionReasoning, ComputerUseReasoning, StandardReasoning
from coreason_manifest.spec.core.flow import (
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    validate_integrity,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, HumanNode, SwarmNode, SwitchNode
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.gatekeeper import _is_guarded, validate_policy
from coreason_manifest.utils.integrity import compute_hash, verify_merkle_proof


# Helper to create common metadata
def get_meta() -> FlowMetadata:
    return FlowMetadata(name="test", version="1.0.0", description="test", tags=[])


def get_defs() -> FlowDefinitions:
    # Profile with Computer Use
    p_comp = CognitiveProfile(
        role="worker",
        persona="worker",
        reasoning=ComputerUseReasoning(model="gpt-4", interaction_mode="native_os", coordinate_system="normalized_0_1"),
        fast_path=None,
    )
    # Safe Profile
    p_safe = CognitiveProfile(role="safe", persona="safe", reasoning=StandardReasoning(model="gpt-3.5"), fast_path=None)
    # Profile with Code Execution
    p_code = CognitiveProfile(
        role="coder",
        persona="coder",
        reasoning=CodeExecutionReasoning(model="gpt-4", allow_network=False, timeout_seconds=30.0),
        fast_path=None,
    )
    return FlowDefinitions(profiles={"comp": p_comp, "safe": p_safe, "code": p_code})


def test_code_execution_unguarded() -> None:
    defs = get_defs()
    node = AgentNode(id="a1", metadata={}, type="agent", profile="code", tools=[])

    flow = LinearFlow(kind="LinearFlow", metadata=get_meta(), definitions=defs, steps=[node])

    errors = validate_policy(flow)
    assert len(errors) == 1
    assert "code_execution" in errors[0].message


def test_base_reasoning_capabilities() -> None:
    # Case: StandardReasoning (inherits BaseReasoning)
    defs = get_defs()
    node = AgentNode(id="a1", metadata={}, type="agent", profile="safe", tools=[])

    flow = LinearFlow(kind="LinearFlow", metadata=get_meta(), definitions=defs, steps=[node])

    # Should call StandardReasoning.required_capabilities() -> []
    errors = validate_policy(flow)
    assert len(errors) == 0


def test_linear_unguarded_computer_use() -> None:
    defs = get_defs()
    # Unguarded AgentNode using "comp" profile
    node = AgentNode(id="a1", metadata={}, type="agent", profile="comp", tools=[])

    flow = LinearFlow(kind="LinearFlow", metadata=get_meta(), definitions=defs, steps=[node])

    errors = validate_policy(flow)
    assert len(errors) == 1
    assert "requires high-risk features (computer_use capability)" in errors[0].message
    assert "not guarded by a HumanNode" in errors[0].message


def test_linear_guarded_computer_use() -> None:
    defs = get_defs()
    human = HumanNode(id="h1", metadata={}, type="human", prompt="ok?", timeout_seconds=10)
    node = AgentNode(id="a1", metadata={}, type="agent", profile="comp", tools=[])

    flow = LinearFlow(kind="LinearFlow", metadata=get_meta(), definitions=defs, steps=[human, node])

    errors = validate_policy(flow)
    assert len(errors) == 0


def test_linear_switch_bypass_fails() -> None:
    # SwitchNode should NOT count as guard
    defs = get_defs()
    switch = SwitchNode(id="s1", metadata={}, type="switch", variable="x", cases={}, default="a1")
    node = AgentNode(id="a1", metadata={}, type="agent", profile="comp", tools=[])

    flow = LinearFlow(kind="LinearFlow", metadata=get_meta(), definitions=defs, steps=[switch, node])

    errors = validate_policy(flow)
    assert len(errors) == 1  # Still fails because Switch is not Human


def test_linear_missing_node_exception() -> None:
    # Force ValueError in _is_guarded by checking a node not in sequence
    pass


def test_swarm_unguarded() -> None:
    defs = get_defs()
    # SwarmNode using "comp" worker profile
    swarm = SwarmNode(
        id="swarm1",
        metadata={},
        type="swarm",
        worker_profile="comp",  # Dangerous profile
        workload_variable="v",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="vote",
        output_variable="out",
    )

    flow = LinearFlow(kind="LinearFlow", metadata=get_meta(), definitions=defs, steps=[swarm])

    errors = validate_policy(flow)
    assert len(errors) == 1
    assert "requires high-risk features" in errors[0].message


def test_swarm_missing_profile_validation() -> None:
    # SwarmNode pointing to missing profile should raise ManifestError when validated
    defs = get_defs()
    swarm = SwarmNode(
        id="swarm1",
        metadata={},
        type="swarm",
        worker_profile="missing",
        workload_variable="v",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="vote",
        output_variable="out",
    )
    flow = LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=get_meta(),
        definitions=defs,
        steps=[swarm],
    )
    # Manual integrity check (since LinearFlow doesn't enforce it automatically)
    with pytest.raises(ManifestError, match="references missing profile"):
        validate_integrity(defs, flow.steps)


def test_gatekeeper_robustness_missing_profile() -> None:
    # Use model_construct to bypass validation and test gatekeeper logic
    defs = get_defs()
    swarm = SwarmNode(
        id="swarm1",
        metadata={},
        type="swarm",
        worker_profile="missing",
        workload_variable="v",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="vote",
        output_variable="out",
    )
    flow = LinearFlow.model_construct(kind="LinearFlow", metadata=get_meta(), definitions=defs, steps=[swarm])
    # Gatekeeper handles missing profile gracefully (no capabilities found)
    errors = validate_policy(flow)
    assert len(errors) == 0


def test_graph_unguarded_path() -> None:
    defs = get_defs()
    # Entry -> Agent(comp) -> End
    # No human
    agent = AgentNode(id="a1", metadata={}, type="agent", profile="comp", tools=[])

    graph = Graph(nodes={"a1": agent}, edges=[], entry_point="a1")

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=get_meta(),
        definitions=defs,
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    errors = validate_policy(flow)
    assert len(errors) == 1  # a1 is entry and unguarded


def test_graph_guarded_path() -> None:
    defs = get_defs()
    # Entry(Human) -> Agent(comp)
    human = HumanNode(id="h1", metadata={}, type="human", prompt="ok?", timeout_seconds=10)
    agent = AgentNode(id="a1", metadata={}, type="agent", profile="comp", tools=[])

    graph = Graph(nodes={"h1": human, "a1": agent}, edges=[Edge(from_node="h1", to_node="a1")], entry_point="h1")

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=get_meta(),
        definitions=defs,
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    errors = validate_policy(flow)
    assert len(errors) == 0


def test_graph_cycle_explicit_entry() -> None:
    # Cyclic graph with explicit entry point
    # a1(comp) -> a1
    # Cycle detection is now enforced only for Published flows.
    defs = get_defs()
    agent = AgentNode(id="a1", metadata={}, type="agent", profile="comp", tools=[])
    graph = Graph(nodes={"a1": agent}, edges=[Edge(from_node="a1", to_node="a1")], entry_point="a1")

    # Should fail when publishing
    # Architectural Update: Cycles are no longer strictly banned by GraphFlow validation.
    # They are flagged by Gatekeeper.
    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=get_meta(),
        definitions=defs,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )
    assert flow.status == "published"


def test_integrity_compute_hash_variants() -> None:
    # Test object with compute_hash method
    class HasMethod:
        def compute_hash(self) -> str:
            return "hash_method"

    assert compute_hash(HasMethod()) == "hash_method"

    # Test Pydantic model
    class MyModel(BaseModel):
        val: int

    m = MyModel(val=1)
    # Pydantic v2 has model_dump_json
    h = compute_hash(m)
    assert len(h) == 64

    # Test fallback
    class PlainObj:
        def __str__(self) -> str:
            return "plain"

    # Architectural Note: Strict integrity ensures we don't silently fallback to str()
    with pytest.raises(TypeError, match="is not deterministically serializable"):
        compute_hash(PlainObj())


def test_gatekeeper_inline_profile() -> None:
    # Gatekeeper L35: reasoning = node.profile.reasoning
    profile = CognitiveProfile(
        role="worker", persona="worker", reasoning=StandardReasoning(model="gpt-3.5"), fast_path=None
    )
    node = AgentNode(
        id="a1",
        metadata={},
        type="agent",
        profile=profile,  # Inline profile
        tools=[],
    )

    flow = LinearFlow(kind="LinearFlow", metadata=get_meta(), definitions=None, steps=[node])

    errors = validate_policy(flow)
    assert len(errors) == 0


def test_gatekeeper_is_guarded_value_error() -> None:
    # Gatekeeper L78-79: except ValueError: return False
    node1 = AgentNode(id="a1", metadata={}, type="agent", profile="p1", tools=[])
    node2 = AgentNode(id="a2", metadata={}, type="agent", profile="p1", tools=[])

    # Use model_construct to bypass referential integrity validation (missing profile p1)
    flow = LinearFlow.model_construct(
        kind="LinearFlow", metadata=get_meta(), definitions=FlowDefinitions(), steps=[node1]
    )

    # Check node2 which is NOT in flow.sequence
    assert _is_guarded(node2, flow) is False


def test_integrity_empty_chain() -> None:
    # Integrity L40: if not chain: return False
    assert verify_merkle_proof([]) is False


def test_gatekeeper_attribute_error() -> None:
    # Gatekeeper L50-52: except AttributeError: return []
    class BrokenReasoning:
        @property
        def required_capabilities(self) -> None:
            raise AttributeError("mock")

    class MockProfile:
        role = "r"
        persona = "p"
        fast_path = None
        reasoning = BrokenReasoning()

    node = AgentNode.model_construct(
        id="a1",
        metadata={},
        type="agent",
        profile=MockProfile(),  # type: ignore
        tools=[],
    )

    flow = LinearFlow.model_construct(kind="LinearFlow", metadata=get_meta(), definitions=None, steps=[node])

    errors = validate_policy(flow)
    assert len(errors) == 0


def test_graph_traversal_unguarded() -> None:
    # Hit neighbor expansion in BFS
    # a1 (entry, safe) -> a2 (target, comp)

    p_comp = CognitiveProfile(
        role="worker",
        persona="worker",
        reasoning=ComputerUseReasoning(model="gpt-4", interaction_mode="native_os", coordinate_system="normalized_0_1"),
        fast_path=None,
    )
    p_safe = CognitiveProfile(role="safe", persona="safe", reasoning=StandardReasoning(model="gpt-3.5"), fast_path=None)
    defs = FlowDefinitions(profiles={"comp": p_comp, "safe": p_safe})

    a1 = AgentNode(id="a1", metadata={}, type="agent", profile="safe", tools=[])
    a2 = AgentNode(id="a2", metadata={}, type="agent", profile="comp", tools=[])

    graph = Graph(nodes={"a1": a1, "a2": a2}, edges=[Edge(from_node="a1", to_node="a2")], entry_point="a1")

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=get_meta(),
        definitions=defs,
        interface=FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        ),
        blackboard=None,
        graph=graph,
    )

    errors = validate_policy(flow)
    assert len(errors) == 1
    assert "not guarded" in errors[0].message


def test_unknown_flow_type() -> None:
    # Hit final return False in _is_guarded
    class UnknownFlow:
        pass

    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[])
    assert _is_guarded(node, UnknownFlow()) is False  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__])


def test_circuit_breaker_timeout_logic() -> None:
    """Cover lines 125-126 and 129 in governance.py."""
    import time

    from coreason_manifest.spec.core.governance import (
        CircuitBreaker,
        CircuitOpenError,
        CircuitState,
        check_circuit,
    )

    policy = CircuitBreaker(error_threshold_count=1, reset_timeout_seconds=2)
    state_store = {"node_1": CircuitState(state="open", failure_count=1, last_failure_time=time.time())}

    # Case 1: Timeout NOT expired
    with pytest.raises(CircuitOpenError):
        check_circuit("node_1", policy, state_store)

    # Case 2: Timeout EXPIRED
    # Force unwrap optional for test logic, or assert it's not None
    last_failure = state_store["node_1"].last_failure_time
    assert last_failure is not None
    state_store["node_1"] = state_store["node_1"].model_copy(update={"last_failure_time": last_failure - 3})
    check_circuit("node_1", policy, state_store)
    assert state_store["node_1"].state == "half-open"


def test_circuit_breaker_record_failure_coverage() -> None:
    """Cover initialization and early return in record_failure."""
    import time

    from coreason_manifest.spec.core.governance import (
        CircuitBreaker,
        CircuitState,
        record_failure,
    )

    policy = CircuitBreaker(error_threshold_count=2, reset_timeout_seconds=1)
    state_store: dict[str, CircuitState] = {}

    # 1. New Node (Init logic)
    record_failure("new_node", policy, state_store)
    assert "new_node" in state_store
    assert state_store["new_node"].failure_count == 1

    # 2. Open Circuit (Early return logic)
    # Trip it
    record_failure("new_node", policy, state_store)  # count=2 -> open
    assert state_store["new_node"].state == "open"
    last_fail = state_store["new_node"].last_failure_time

    # Call again - should return early and NOT update time or count
    time.sleep(0.1)
    record_failure("new_node", policy, state_store)
    assert state_store["new_node"].last_failure_time == last_fail  # Unchanged
