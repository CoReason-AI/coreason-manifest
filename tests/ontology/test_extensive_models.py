# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Extensive model instantiation tests for comprehensive coverage.

Constructs verified instances of many models to exercise init, field_validators,
and model_validators that only run during actual construction.
"""

from coreason_manifest.spec.ontology import (
    # Simple models with minimal required fields
    AmbientState,
    BoundedInterventionScopePolicy,
    BoundedJSONRPCIntent,
    CausalAttributionState,
    CognitiveAgentNodeProfile,
    CognitiveCritiqueProfile,
    # SOP
    CognitiveStateProfile,
    CognitiveSystemNodeProfile,
    CollectiveIntelligenceProfile,
    ComputeProvisioningIntent,
    ComputeRateContract,
    ConsensusPolicy,
    ConstitutionalAmendmentIntent,
    ContextualizedSourceState,
    ContinuousMutationPolicy,
    # Slightly more complex
    CouncilTopologyManifest,
    # Provenance
    CryptographicProvenancePolicy,
    CrystallizationPolicy,
    DAGTopologyManifest,
    DifferentiableLogicPolicy,
    DiscourseNodeState,
    DistributionProfile,
    DiversityPolicy,
    DocumentLayoutRegionState,
    DynamicConvergenceSLA,
    EdgeMappingContract,
    EmbodiedSensoryVectorProfile,
    # Facet
    FacetMatrixProfile,
    # FYI
    FYIIntent,
    # Multi-modal token anchor
    MultimodalTokenAnchorState,
)


class TestSimpleModels:
    """Construct models with simple scalar required fields."""

    def test_ambient_state(self) -> None:
        obj = AmbientState(status_message="active")
        assert obj.status_message == "active"

    def test_causal_attribution(self) -> None:
        obj = CausalAttributionState(source_event_cid="ev-1", influence_weight=0.7)
        assert obj.influence_weight == 0.7

    def test_cognitive_critique(self) -> None:
        obj = CognitiveCritiqueProfile(reasoning_trace_hash="a" * 64, epistemic_penalty_scalar=0.1)
        assert obj.epistemic_penalty_scalar == 0.1

    def test_cognitive_state(self) -> None:
        obj = CognitiveStateProfile(urgency_index=0.5, caution_index=0.3, divergence_tolerance=0.2)
        assert obj.urgency_index == 0.5

    def test_collective_intelligence(self) -> None:
        obj = CollectiveIntelligenceProfile(synergy_index=0.8, coordination_score=0.7, information_integration=0.9)
        assert obj.synergy_index == 0.8

    def test_consensus_policy(self) -> None:
        obj = ConsensusPolicy(strategy="majority")
        assert obj.strategy == "majority"

    def test_compute_rate_contract(self) -> None:
        obj = ComputeRateContract(
            cost_per_million_input_tokens=100,
            cost_per_million_output_tokens=300,
            magnitude_unit="usd_cents",
        )
        assert obj.cost_per_million_output_tokens == 300

    def test_constitutional_amendment(self) -> None:
        obj = ConstitutionalAmendmentIntent(
            drift_event_cid="drift-1",
            proposed_patch={"key": "value"},
            justification="fix bug",
        )
        assert obj.drift_event_cid == "drift-1"

    def test_contextualized_source(self) -> None:
        obj = ContextualizedSourceState(
            target_string="test",
            contextual_envelope=["context1"],
            source_system_provenance_flag=True,
        )
        assert obj.source_system_provenance_flag is True

    def test_continuous_mutation(self) -> None:
        obj = ContinuousMutationPolicy(
            mutation_paradigm="append_only",
            max_uncommitted_edges=100,
            micro_batch_interval_ms=500,
        )
        assert obj.mutation_paradigm == "append_only"

    def test_crystallization_policy(self) -> None:
        obj = CrystallizationPolicy(
            min_observations_required=10,
            aleatoric_entropy_threshold=0.1,
            target_cognitive_tier="semantic",
        )
        assert obj.min_observations_required == 10

    def test_differentiable_logic(self) -> None:
        obj = DifferentiableLogicPolicy(
            constraint_cid="c-1",
            formal_syntax_smt="(assert true)",
            relaxation_epsilon=0.01,
        )
        assert obj.relaxation_epsilon == 0.01

    def test_distribution_profile(self) -> None:
        obj = DistributionProfile(distribution_type="gaussian")
        assert obj.distribution_type == "gaussian"

    def test_diversity_policy(self) -> None:
        obj = DiversityPolicy(min_adversaries=2, model_variance_required=True)
        assert obj.min_adversaries == 2

    def test_dynamic_convergence_sla(self) -> None:
        obj = DynamicConvergenceSLA(
            convergence_delta_epsilon=0.001,
            lookback_window_steps=10,
            minimum_reasoning_steps=5,
        )
        assert obj.lookback_window_steps == 10

    def test_edge_mapping_contract(self) -> None:
        obj = EdgeMappingContract(source_pointer="/input", target_pointer="/output")
        assert obj.source_pointer == "/input"

    def test_embodied_sensory_vector(self) -> None:
        obj = EmbodiedSensoryVectorProfile(
            sensory_modality="audio",
            bayesian_surprise_score=0.7,
            temporal_duration_ms=1000,
        )
        assert obj.sensory_modality == "audio"

    def test_bounded_jsonrpc(self) -> None:
        obj = BoundedJSONRPCIntent(jsonrpc="2.0", method="test_method")
        assert obj.method == "test_method"

    def test_bounded_intervention_scope(self) -> None:
        obj = BoundedInterventionScopePolicy(
            allowed_fields=["field_a"],
            json_schema_whitelist={"type": "object"},
        )
        assert len(obj.allowed_fields) == 1

    def test_compute_provisioning(self) -> None:
        obj = ComputeProvisioningIntent(
            max_budget=5000,
            required_capabilities=["gpu", "inference"],
        )
        assert obj.max_budget == 5000

    def test_fyi_intent(self) -> None:
        obj = FYIIntent()
        assert obj is not None

    def test_facet_matrix(self) -> None:
        obj = FacetMatrixProfile()
        assert obj is not None

    def test_cryptographic_provenance(self) -> None:
        obj = CryptographicProvenancePolicy()
        assert obj is not None


class TestTopologyInstantiation:
    """Construct topology models with nodes."""

    def test_council_topology(self) -> None:
        obj = CouncilTopologyManifest(
            nodes={
                "did:z:agent1": CognitiveAgentNodeProfile(description="agent"),
                "did:z:adj": CognitiveSystemNodeProfile(description="adjudicator"),
            },
            adjudicator_cid="did:z:adj",
        )
        assert len(obj.nodes) == 2

    def test_dag_topology_basic(self) -> None:
        obj = DAGTopologyManifest(
            nodes={
                "did:z:n1": CognitiveAgentNodeProfile(description="node 1"),
                "did:z:n2": CognitiveSystemNodeProfile(description="node 2"),
            },
            max_depth=5,
            max_fan_out=3,
        )
        assert obj.max_depth == 5


class TestDocumentModels:
    """Construct document-related models."""

    def test_document_layout_region(self) -> None:
        anchor = MultimodalTokenAnchorState()
        obj = DocumentLayoutRegionState(
            block_cid="block-1",
            block_class="paragraph",
            anchor=anchor,
        )
        assert obj.block_class == "paragraph"

    def test_discourse_node_types(self) -> None:
        """Exercise different discourse types for coverage."""
        for dtype in ["preamble", "methodology", "argumentation", "findings", "conclusion", "addendum"]:
            obj = DiscourseNodeState(node_cid=f"did:z:{dtype}", discourse_type=dtype)  # type: ignore[arg-type]
            assert obj.discourse_type == dtype


