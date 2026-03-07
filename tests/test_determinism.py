# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from coreason_manifest.compute.stochastic import CrossoverStrategy, FitnessObjective, MutationPolicy
from coreason_manifest.oversight.dlp import InformationFlowPolicy, RedactionRule
from coreason_manifest.presentation.intents import InformationalIntent
from coreason_manifest.presentation.scivis import ChannelEncoding, GrammarPanel
from coreason_manifest.state.argumentation import ArgumentClaim, ArgumentGraph, DefeasibleAttack
from coreason_manifest.state.differentials import RollbackRequest
from coreason_manifest.state.events import ObservationEvent
from coreason_manifest.state.memory import EpistemicLedger
from coreason_manifest.state.semantic import (
    MemoryProvenance,
    SalienceProfile,
    SemanticNode,
    TemporalBounds,
    VectorEmbedding,
)
from coreason_manifest.telemetry.schemas import ExecutionSpan, SpanEvent, TraceExportBatch
from coreason_manifest.testing.chaos import ChaosExperiment, FaultInjectionProfile, SteadyStateHypothesis
from coreason_manifest.tooling import ActionSpace, PermissionBoundary, SideEffectProfile, ToolDefinition
from coreason_manifest.workflow.auctions import AgentBid, AuctionState, TaskAnnouncement
from coreason_manifest.workflow.envelope import WorkflowEnvelope
from coreason_manifest.workflow.nodes import AgentNode, CompositeNode
from coreason_manifest.workflow.topologies import DAGTopology, EvolutionaryTopology, SwarmTopology


def test_composite_node_determinism() -> None:
    # Encapsulated swarm topology
    swarm_top1 = SwarmTopology(
        nodes={"agent_1": AgentNode(description="worker")},
        spawning_threshold=2,
        max_concurrent_agents=5,
    )
    swarm_top2 = SwarmTopology(
        nodes={"agent_1": AgentNode(description="worker")},
        spawning_threshold=2,
        max_concurrent_agents=5,
    )

    composite_node1 = CompositeNode(
        description="A nested graph",
        topology=swarm_top1,
        input_mappings=[],
        output_mappings=[],
    )
    composite_node2 = CompositeNode(
        description="A nested graph",
        topology=swarm_top2,
        input_mappings=[],
        output_mappings=[],
    )

    dag1 = DAGTopology(
        nodes={"comp_1": composite_node1},
        allow_cycles=False,
    )
    dag2 = DAGTopology(
        nodes={"comp_1": composite_node2},
        allow_cycles=False,
    )

    assert dag1.model_dump_canonical() == dag2.model_dump_canonical()
    assert hash(dag1) == hash(dag2)


def test_workflow_envelope_determinism() -> None:
    node1 = AgentNode(description="First node")
    node2 = AgentNode(description="Second node")
    topology1 = DAGTopology(
        nodes={"node_a": node1, "node_b": node2},
        allow_cycles=False,
        backpressure=None,
        shared_state_contract=None,
    )
    topology2 = DAGTopology(
        nodes={"node_b": node2, "node_a": node1},
        allow_cycles=False,
        backpressure=None,
        shared_state_contract=None,
    )

    env1 = WorkflowEnvelope(manifest_version="1.0.0", topology=topology1)
    env2 = WorkflowEnvelope(manifest_version="1.0.0", topology=topology2)

    assert env1.model_dump_canonical() == env2.model_dump_canonical()
    assert hash(env1) == hash(env2)


def test_lazy_hashing_performance_and_coverage() -> None:
    """
    Prove that CoreasonBaseModel uses lazy hashing.
    It should not have a _cached_hash upon instantiation, but should compute
    and store it when hash() is explicitly called, hitting the AttributeError fallback.
    """
    from coreason_manifest.workflow.nodes import SystemNode

    # Instantiate a frozen model
    node = SystemNode(description="Test lazy hash")

    # 1. Prove the hash is NOT eagerly computed (saves performance)
    assert not hasattr(node, "_cached_hash")

    # 2. Trigger the __hash__ method (hits the except AttributeError block)
    first_hash = hash(node)

    # 3. Prove the hash is now cached
    assert hasattr(node, "_cached_hash")

    # 4. Trigger the __hash__ method again (hits the try block)
    second_hash = hash(node)

    # 5. Prove determinism and cache retrieval
    assert first_hash == second_hash


def test_telemetry_determinism() -> None:
    event_late = SpanEvent(name="late_event", timestamp_unix_nano=200, attributes={})
    event_early = SpanEvent(name="early_event", timestamp_unix_nano=100, attributes={})

    span_b = ExecutionSpan(
        trace_id="t1",
        span_id="s_b",
        name="span_b",
        start_time_unix_nano=100,
        events=[event_late, event_early],
    )
    span_a = ExecutionSpan(
        trace_id="t1",
        span_id="s_a",
        name="span_a",
        start_time_unix_nano=100,
        events=[event_early, event_late],
    )

    batch1 = TraceExportBatch(batch_id="b1", spans=[span_a, span_b])
    batch2 = TraceExportBatch(batch_id="b1", spans=[span_b, span_a])

    assert batch1.model_dump_canonical() == batch2.model_dump_canonical()
    assert hash(batch1) == hash(batch2)


def test_evolutionary_determinism() -> None:
    obj_acc = FitnessObjective(target_metric="accuracy", direction="maximize", weight=0.8)
    obj_cost = FitnessObjective(target_metric="cost", direction="minimize", weight=0.2)

    mutation_policy = MutationPolicy(mutation_rate=0.1, temperature_shift_variance=0.2)
    crossover_strategy = CrossoverStrategy(strategy_type="uniform_blend", blending_factor=0.5)

    top1 = EvolutionaryTopology(
        nodes={},
        generations=10,
        population_size=100,
        mutation=mutation_policy,
        crossover=crossover_strategy,
        fitness_objectives=[obj_acc, obj_cost],
    )

    top2 = EvolutionaryTopology(
        nodes={},
        generations=10,
        population_size=100,
        mutation=mutation_policy,
        crossover=crossover_strategy,
        fitness_objectives=[obj_cost, obj_acc],
    )

    assert top1.model_dump_canonical() == top2.model_dump_canonical()
    assert hash(top1) == hash(top2)


def test_rollback_determinism() -> None:
    req1 = RollbackRequest(request_id="r1", target_event_id="e_3", invalidated_node_ids=["node_z", "node_a", "node_k"])
    req2 = RollbackRequest(request_id="r1", target_event_id="e_3", invalidated_node_ids=["node_k", "node_z", "node_a"])

    assert req1.model_dump_canonical() == req2.model_dump_canonical()
    assert hash(req1) == hash(req2)


def test_dlp_determinism() -> None:
    rule_a = RedactionRule(
        rule_id="a_phi_redact",
        classification="phi",
        target_pattern="pattern_a",
        target_regex_pattern="pattern_a",
        action="redact",
        replacement_token="[REDACTED]",  # noqa: S106
    )
    rule_b = RedactionRule(
        rule_id="b_pii_hash",
        classification="pii",
        target_pattern="pattern_b",
        target_regex_pattern="pattern_b",
        action="hash",
    )

    policy1 = InformationFlowPolicy(policy_id="p1", rules=[rule_a, rule_b])
    policy2 = InformationFlowPolicy(policy_id="p1", rules=[rule_b, rule_a])

    assert policy1.model_dump_canonical() == policy2.model_dump_canonical()
    assert hash(policy1) == hash(policy2)


def test_auction_determinism() -> None:
    ann = TaskAnnouncement(task_id="t1", max_budget_cents=10000)

    bid_1 = AgentBid(agent_id="agent_a", estimated_cost_cents=1000, estimated_latency_ms=100, confidence_score=0.9)
    bid_2 = AgentBid(agent_id="agent_b", estimated_cost_cents=1200, estimated_latency_ms=90, confidence_score=0.85)
    bid_3 = AgentBid(agent_id="agent_c", estimated_cost_cents=900, estimated_latency_ms=110, confidence_score=0.95)

    state1 = AuctionState(announcement=ann, bids=[bid_1, bid_2, bid_3])
    state2 = AuctionState(announcement=ann, bids=[bid_3, bid_1, bid_2])

    assert state1.model_dump_canonical() == state2.model_dump_canonical()
    assert hash(state1) == hash(state2)


def test_argumentation_determinism() -> None:
    claim1 = ArgumentClaim(
        claim_id="claim_1", proponent_id="agent_x", text_chunk="This sentence is false.", warrants=[]
    )
    claim2 = ArgumentClaim(
        claim_id="claim_2", proponent_id="agent_y", text_chunk="The previous sentence is true.", warrants=[]
    )

    attack1 = DefeasibleAttack(
        attack_id="attack_1", source_claim_id="claim_1", target_claim_id="claim_2", attack_vector="rebuttal"
    )
    attack2 = DefeasibleAttack(
        attack_id="attack_2", source_claim_id="claim_2", target_claim_id="claim_1", attack_vector="undercutter"
    )

    graph1 = ArgumentGraph(
        claims={"claim_1": claim1, "claim_2": claim2},
        attacks={"attack_1": attack1, "attack_2": attack2},
    )

    graph2 = ArgumentGraph(
        claims={"claim_2": claim2, "claim_1": claim1},
        attacks={"attack_2": attack2, "attack_1": attack1},
    )

    assert graph1.model_dump_canonical() == graph2.model_dump_canonical()
    assert hash(graph1) == hash(graph2)


def test_tooling_determinism() -> None:
    side_effects = SideEffectProfile(is_idempotent=True, mutates_state=False)
    permissions = PermissionBoundary(network_access=False, allowed_domains=None, file_system_read_only=True)

    tool1 = ToolDefinition(
        tool_name="my_tool",
        description="A deterministic tool",
        input_schema={"a": 1, "b": 2},
        side_effects=side_effects,
        permissions=permissions,
    )

    tool2 = ToolDefinition(
        tool_name="my_tool",
        description="A deterministic tool",
        input_schema={"b": 2, "a": 1},
        side_effects=side_effects,
        permissions=permissions,
    )

    space1 = ActionSpace(action_space_id="space_1", native_tools=[tool1], mcp_servers=[])
    space2 = ActionSpace(action_space_id="space_1", native_tools=[tool2], mcp_servers=[])

    assert space1.model_dump_canonical() == space2.model_dump_canonical()
    assert hash(space1) == hash(space2)


def test_grammar_determinism() -> None:
    enc_x = ChannelEncoding(channel="x", field="date")
    enc_color = ChannelEncoding(channel="color", field="category")

    panel1 = GrammarPanel(
        panel_id="p1",
        title="T",
        data_source_id="d1",
        mark="point",
        encodings=[enc_x, enc_color],
    )

    panel2 = GrammarPanel(
        panel_id="p1",
        title="T",
        data_source_id="d1",
        mark="point",
        encodings=[enc_color, enc_x],  # Simulated out-of-order generation
    )

    assert panel1.model_dump_canonical() == panel2.model_dump_canonical()
    assert hash(panel1) == hash(panel2)


def test_presentation_intent_determinism() -> None:
    intent1 = InformationalIntent(message="Message 1", timeout_action="rollback")
    intent2 = InformationalIntent(message="Message 1", timeout_action="rollback")

    assert intent1.model_dump_canonical() == intent2.model_dump_canonical()
    assert hash(intent1) == hash(intent2)


def test_epistemic_ledger_determinism() -> None:
    event1 = ObservationEvent(event_id="obs_1", timestamp=100.0, payload={})
    event2 = ObservationEvent(event_id="obs_2", timestamp=200.0, payload={})

    ledger1 = EpistemicLedger(history=[event1, event2])
    ledger2 = EpistemicLedger(history=[event1, event2])

    assert ledger1.model_dump_canonical() == ledger2.model_dump_canonical()
    assert hash(ledger1) == hash(ledger2)


def test_epistemic_payload_canonical_hashing() -> None:
    data = {"temperature": 72, "humidity": 0.5, "status": "nominal"}
    scrambled_data = {"status": "nominal", "temperature": 72, "humidity": 0.5}

    event_a = ObservationEvent(event_id="obs_1", timestamp=100.0, payload=data)
    event_b = ObservationEvent(event_id="obs_1", timestamp=100.0, payload=scrambled_data)

    assert hash(event_a) == hash(event_b)
    assert event_a.model_dump_canonical() == event_b.model_dump_canonical()


def test_semantic_memory_determinism() -> None:
    embedding = VectorEmbedding(vector=[0.1, 0.2, 0.3], dimensionality=3, model_name="test-model")
    temporal_bounds = TemporalBounds(valid_from=100.0, valid_to=200.0, interval_type="overlaps")
    provenance = MemoryProvenance(extracted_by="agent_1", source_event_id="event_1")
    salience = SalienceProfile(baseline_importance=0.9, decay_rate=0.1)

    node1 = SemanticNode(
        node_id="node_1",
        label="Concept",
        text_chunk="A test chunk",
        embedding=embedding,
        provenance=provenance,
        tier="semantic",
        temporal_bounds=temporal_bounds,
        salience=salience,
    )

    node2 = SemanticNode(
        node_id="node_1",
        label="Concept",
        text_chunk="A test chunk",
        embedding=embedding,
        provenance=provenance,
        tier="semantic",
        temporal_bounds=temporal_bounds,
        salience=salience,
    )

    assert node1.model_dump_canonical() == node2.model_dump_canonical()
    assert hash(node1) == hash(node2)


def test_chaos_determinism() -> None:
    fault1 = FaultInjectionProfile(fault_type="latency_spike", target_node_id="node_a", intensity=0.8)
    fault2 = FaultInjectionProfile(fault_type="context_overload", target_node_id="node_b", intensity=0.5)

    hypothesis = SteadyStateHypothesis(expected_max_latency=100.0, max_loops_allowed=5, required_tool_usage=["tool_x"])

    env1 = ChaosExperiment(experiment_id="exp_01", hypothesis=hypothesis, faults=[fault1, fault2])

    env2 = ChaosExperiment(experiment_id="exp_01", hypothesis=hypothesis, faults=[fault1, fault2])

    assert env1.model_dump_canonical() == env2.model_dump_canonical()
    assert hash(env1) == hash(env2)
