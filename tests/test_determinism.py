# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from coreason_manifest import (
    ActionSpace,
    AgentBid,
    AgentNode,
    ArgumentClaim,
    ArgumentGraph,
    AuctionState,
    ChannelEncoding,
    ChaosExperiment,
    CompositeNode,
    CrossoverStrategy,
    DAGTopology,
    DefeasibleAttack,
    DraftingIntent,
    EpistemicLedger,
    EvolutionaryTopology,
    ExecutionSpan,
    FaultInjectionProfile,
    FitnessObjective,
    GrammarPanel,
    InformationFlowPolicy,
    InsightCard,
    MacroGrid,
    MemoryProvenance,
    MutationPolicy,
    ObservationEvent,
    PermissionBoundary,
    PresentationEnvelope,
    RedactionRule,
    RollbackRequest,
    SalienceProfile,
    SemanticNode,
    SideEffectProfile,
    SpanEvent,
    SteadyStateHypothesis,
    SwarmTopology,
    TaskAnnouncement,
    TemporalBounds,
    ToolDefinition,
    TraceExportBatch,
    VectorEmbedding,
    WorkflowEnvelope,
)


def test_compute_topology_hash_determinism() -> None:
    from coreason_manifest import DAGTopology, SystemNode, compute_topology_hash

    node1 = SystemNode(description="Determinism Test")
    topology_a = DAGTopology(nodes={"did:web:node_1": node1}, allow_cycles=False, max_depth=10, max_fan_out=10)
    topology_b = DAGTopology(nodes={"did:web:node_1": node1}, allow_cycles=False, max_depth=10, max_fan_out=10)

    hash_a = compute_topology_hash(topology_a)
    hash_b = compute_topology_hash(topology_b)

    assert hash_a == hash_b
    assert len(hash_a) == 64


def test_composite_node_determinism() -> None:
    # Encapsulated swarm topology
    swarm_top1 = SwarmTopology(
        nodes={"did:web:agent_1": AgentNode(description="worker")},
        spawning_threshold=2,
        max_concurrent_agents=5,
    )
    swarm_top2 = SwarmTopology(
        nodes={"did:web:agent_1": AgentNode(description="worker")},
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

    dag1 = DAGTopology(nodes={"did:web:comp_1": composite_node1}, allow_cycles=False, max_depth=10, max_fan_out=10)
    dag2 = DAGTopology(nodes={"did:web:comp_1": composite_node2}, allow_cycles=False, max_depth=10, max_fan_out=10)

    assert dag1.model_dump_canonical() == dag2.model_dump_canonical()
    assert hash(dag1) == hash(dag2)


def test_workflow_envelope_determinism() -> None:
    node1 = AgentNode(description="First node")
    node2 = AgentNode(description="Second node")
    topology1 = DAGTopology(
        nodes={"did:web:node_a": node1, "did:web:node_b": node2},
        allow_cycles=False,
        backpressure=None,
        shared_state_contract=None,
        max_depth=10,
        max_fan_out=10,
    )
    topology2 = DAGTopology(
        nodes={"did:web:node_b": node2, "did:web:node_a": node1},
        allow_cycles=False,
        backpressure=None,
        shared_state_contract=None,
        max_depth=10,
        max_fan_out=10,
    )

    env1 = WorkflowEnvelope(manifest_version="1.0.0", topology=topology1)
    env2 = WorkflowEnvelope(manifest_version="1.0.0", topology=topology2)

    assert env1.model_dump_canonical() == env2.model_dump_canonical()
    assert hash(env1) == hash(env2)


def test_system2_remediation_determinism() -> None:
    from coreason_manifest import System2RemediationPrompt

    # Prove that out-of-order failing_pointers are sorted mathematically
    prompt1 = System2RemediationPrompt(
        fault_id="fault-123",
        target_node_id="did:web:agent-alpha",
        failing_pointers=["/zeta", "/alpha", "/gamma"],
        remediation_prompt="Fix it.",
    )
    prompt2 = System2RemediationPrompt(
        fault_id="fault-123",
        target_node_id="did:web:agent-alpha",
        failing_pointers=["/gamma", "/zeta", "/alpha"],
        remediation_prompt="Fix it.",
    )

    assert prompt1.model_dump_canonical() == prompt2.model_dump_canonical()
    assert hash(prompt1) == hash(prompt2)


def test_affordance_projection_determinism() -> None:
    from coreason_manifest import ActionSpace, OntologicalSurfaceProjection

    space1 = ActionSpace(action_space_id="s1")
    space2 = ActionSpace(action_space_id="s2")

    proj1 = OntologicalSurfaceProjection(
        projection_id="p1", action_spaces=[space2, space1], supported_personas=["b_persona", "a_persona"]
    )
    proj2 = OntologicalSurfaceProjection(
        projection_id="p1", action_spaces=[space1, space2], supported_personas=["a_persona", "b_persona"]
    )

    assert proj1.model_dump_canonical() == proj2.model_dump_canonical()
    assert hash(proj1) == hash(proj2)


def test_federated_attestation_determinism() -> None:
    from coreason_manifest import BilateralSLA, DataClassification, FederatedCapabilityAttestation, SecureSubSession

    sla = BilateralSLA(
        receiving_tenant_id="tenant_a",
        max_permitted_classification=DataClassification.RESTRICTED,
        liability_limit_magnitude=100,
    )
    session = SecureSubSession(session_id="s1", allowed_vault_keys=["key1"], max_ttl_seconds=3600, description="test")

    att1 = FederatedCapabilityAttestation(
        attestation_id="a1", target_topology_id="did:web:node1", authorized_session=session, governing_sla=sla
    )
    att2 = FederatedCapabilityAttestation(
        attestation_id="a1", target_topology_id="did:web:node1", authorized_session=session, governing_sla=sla
    )

    assert att1.model_dump_canonical() == att2.model_dump_canonical()
    assert hash(att1) == hash(att2)


def test_lazy_hashing_performance_and_coverage() -> None:
    """
    Prove that CoreasonBaseModel uses lazy hashing.
    It should not have a _cached_hash upon instantiation, but should compute
    and store it when hash() is explicitly called, hitting the AttributeError fallback.
    """
    from coreason_manifest import SystemNode

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
    req1 = RollbackRequest(
        request_id="r1",
        target_event_id="e_3",
        invalidated_node_ids=["did:web:node_z", "did:web:node_a", "did:web:node_k"],
    )
    req2 = RollbackRequest(
        request_id="r1",
        target_event_id="e_3",
        invalidated_node_ids=["did:web:node_k", "did:web:node_z", "did:web:node_a"],
    )

    assert req1.model_dump_canonical() == req2.model_dump_canonical()
    assert hash(req1) == hash(req2)


def test_dlp_determinism() -> None:
    from coreason_manifest import DataClassification

    rule_a = RedactionRule(
        rule_id="a_phi_redact",
        classification=DataClassification.RESTRICTED,
        target_pattern="pattern_a",
        target_regex_pattern="pattern_a",
        action="redact",
        replacement_token="[REDACTED]",  # noqa: S106
    )
    rule_b = RedactionRule(
        rule_id="b_pii_hash",
        classification=DataClassification.CONFIDENTIAL,
        target_pattern="pattern_b",
        target_regex_pattern="pattern_b",
        action="hash",
    )

    policy1 = InformationFlowPolicy(policy_id="p1", rules=[rule_a, rule_b])
    policy2 = InformationFlowPolicy(policy_id="p1", rules=[rule_b, rule_a])

    assert policy1.model_dump_canonical() == policy2.model_dump_canonical()
    assert hash(policy1) == hash(policy2)


def test_auction_determinism() -> None:
    ann = TaskAnnouncement(task_id="t1", max_budget_magnitude=10000)

    bid_1 = AgentBid(
        agent_id="did:web:agent_a",
        estimated_cost_magnitude=1000,
        estimated_latency_ms=100,
        estimated_carbon_gco2eq=10.0,
        confidence_score=0.9,
    )
    bid_2 = AgentBid(
        agent_id="did:web:agent_b",
        estimated_cost_magnitude=800,
        estimated_latency_ms=150,
        estimated_carbon_gco2eq=8.0,
        confidence_score=0.95,
    )
    bid_3 = AgentBid(
        agent_id="did:web:agent_c",
        estimated_cost_magnitude=1200,
        estimated_latency_ms=90,
        estimated_carbon_gco2eq=12.0,
        confidence_score=0.8,
    )

    state1 = AuctionState(announcement=ann, bids=[bid_1, bid_2, bid_3], clearing_timeout=10, minimum_tick_size=0.1)
    state2 = AuctionState(announcement=ann, bids=[bid_3, bid_1, bid_2], clearing_timeout=10, minimum_tick_size=0.1)

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


def test_presentation_envelope_determinism() -> None:
    intent1 = DraftingIntent(
        context_prompt="Missing context", resolution_schema={"type": "string"}, timeout_action="rollback"
    )
    intent2 = DraftingIntent(
        context_prompt="Missing context", resolution_schema={"type": "string"}, timeout_action="rollback"
    )

    panel1 = InsightCard(panel_id="panel_1", title="Insight 1", markdown_content="Content 1")
    panel2 = InsightCard(panel_id="panel_2", title="Insight 2", markdown_content="Content 2")

    grid1 = MacroGrid(layout_matrix=[["panel_1", "panel_2"]], panels=[panel1, panel2])
    grid2 = MacroGrid(layout_matrix=[["panel_1", "panel_2"]], panels=[panel1, panel2])

    env1 = PresentationEnvelope(intent=intent1, grid=grid1)
    env2 = PresentationEnvelope(intent=intent2, grid=grid2)

    assert env1.model_dump_canonical() == env2.model_dump_canonical()
    assert hash(env1) == hash(env2)


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
    embedding = VectorEmbedding(vector_base64="dGVzdA==", dimensionality=3, model_name="test-model")
    temporal_bounds = TemporalBounds(valid_from=100.0, valid_to=200.0, interval_type="overlaps")
    provenance = MemoryProvenance(extracted_by="did:web:agent_1", source_event_id="event_1")
    salience = SalienceProfile(baseline_importance=0.9, decay_rate=0.1)

    node1 = SemanticNode(
        node_id="did:web:node_1",
        label="Concept",
        text_chunk="A test chunk",
        embedding=embedding,
        provenance=provenance,
        tier="semantic",
        temporal_bounds=temporal_bounds,
        salience=salience,
    )

    node2 = SemanticNode(
        node_id="did:web:node_1",
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
    fault1 = FaultInjectionProfile(fault_type="latency_spike", target_node_id="did:web:node_a", intensity=0.8)
    fault2 = FaultInjectionProfile(fault_type="context_overload", target_node_id="did:web:node_b", intensity=0.5)

    hypothesis = SteadyStateHypothesis(expected_max_latency=100.0, max_loops_allowed=5, required_tool_usage=["tool_x"])

    env1 = ChaosExperiment(experiment_id="exp_01", hypothesis=hypothesis, faults=[fault1, fault2])

    env2 = ChaosExperiment(experiment_id="exp_01", hypothesis=hypothesis, faults=[fault1, fault2])

    assert env1.model_dump_canonical() == env2.model_dump_canonical()
    assert hash(env1) == hash(env2)
