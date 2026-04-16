# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Bulk instantiation tests for uncovered Pydantic models.

Provides systematic coverage for validator branches via minimal
construction of validated models.
"""

import time

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    # Activation Steering
    ActivationSteeringContract,
    # Active Inference
    ActiveInferenceContract,
    # Attestation
    AgentAttestationReceipt,
    # Assertion AST
    AuctionPolicy,
    # Backpressure
    BackpressurePolicy,
    # Belief
    BeliefMutationEvent,
    # Browser
    BrowserDOMState,
    # Causal
    CausalDirectedEdgeState,
    # Circuit Breaker
    CircuitBreakerEvent,
    # Agents
    CognitiveAgentNodeProfile,
    # Format
    CognitiveFormatContract,
    CognitiveHumanNodeProfile,
    # Routing
    CognitiveRoutingContract,
    # Sampling
    CognitiveSamplingPolicy,
    CognitiveSystemNodeProfile,
    # Context expansion
    ContextExpansionPolicy,
    # Cyclic edge
    CyclicEdgeProfile,
    # Adjudication
    GradingCriterionProfile,
    # Kinetic separation
    KineticSeparationPolicy,
    # Routing
    RoutingFrontierPolicy,
    # SAE
    ScalePolicy,
    # Terminal condition
    TerminalConditionContract,
)

# ---------------------------------------------------------------------------
# ScalePolicy — validate_domain branches
# ---------------------------------------------------------------------------


class TestScalePolicy:
    """Exercise ScalePolicy model_validator branches."""

    def test_valid_linear(self) -> None:
        sp = ScalePolicy(topology_class="linear", domain_min=0.0, domain_max=100.0)
        assert sp.domain_min < sp.domain_max  # type: ignore[operator]

    def test_domain_min_gt_max_rejected(self) -> None:
        with pytest.raises(ValidationError, match="domain_min cannot be"):
            ScalePolicy(topology_class="linear", domain_min=100.0, domain_max=0.0)

    def test_zero_length_continuous_rejected(self) -> None:
        with pytest.raises(ValidationError, match="zero for continuous"):
            ScalePolicy(topology_class="log", domain_min=10.0, domain_max=10.0)

    def test_log_negative_min_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strictly positive"):
            ScalePolicy(topology_class="log", domain_min=-1.0)

    def test_log_negative_max_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ScalePolicy(topology_class="log", domain_min=1.0, domain_max=-5.0)

    def test_ordinal_scale_valid(self) -> None:
        sp = ScalePolicy(topology_class="ordinal")
        assert sp.topology_class == "ordinal"


# ---------------------------------------------------------------------------
# RoutingFrontierPolicy — _clamp_frontier_bounds_before
# ---------------------------------------------------------------------------


class TestRoutingFrontierPolicy:
    """Exercise the _clamp_frontier_bounds_before mode='before' validator."""

    def test_valid_frontier(self) -> None:
        obj = RoutingFrontierPolicy(
            max_latency_ms=100,
            max_cost_magnitude_per_token=50,
            min_capability_score=0.5,
            tradeoff_preference="latency_optimized",
        )
        assert obj.max_latency_ms == 100

    def test_clamped_latency(self) -> None:
        """Negative latency gets clamped to 1."""
        obj = RoutingFrontierPolicy(
            max_latency_ms=-10,
            max_cost_magnitude_per_token=50,
            min_capability_score=0.5,
            tradeoff_preference="latency_optimized",
        )
        assert obj.max_latency_ms >= 1

    def test_clamped_capability_score(self) -> None:
        """Capability score > 1.0 gets clamped to 1.0."""
        obj = RoutingFrontierPolicy(
            max_latency_ms=100,
            max_cost_magnitude_per_token=50,
            min_capability_score=2.0,
            tradeoff_preference="cost_optimized",
        )
        assert obj.min_capability_score <= 1.0

    def test_carbon_intensity_clamped(self) -> None:
        obj = RoutingFrontierPolicy(
            max_latency_ms=100,
            max_cost_magnitude_per_token=50,
            min_capability_score=0.5,
            tradeoff_preference="carbon_optimized",
            max_carbon_intensity_gco2eq_kwh=-1.0,
        )
        assert obj.max_carbon_intensity_gco2eq_kwh >= 0.0  # type: ignore[operator]


# ---------------------------------------------------------------------------
# CyclicEdgeProfile — prevent_infinite_loop
# ---------------------------------------------------------------------------


class TestCyclicEdgeProfile:
    """Exercise prevent_infinite_loop validator."""

    def test_valid_cyclic_edge(self) -> None:
        obj = CyclicEdgeProfile(
            target_node_cid="target",
            probability_weight=0.5,
            compute_weight_magnitude=1,
            discount_factor=0.9,
            terminal_condition=TerminalConditionContract(
                max_causal_depth=10,
            ),
        )
        assert obj.discount_factor == 0.9

    def test_infinite_loop_rejected(self) -> None:
        with pytest.raises(ValidationError, match="infinite loop"):
            CyclicEdgeProfile(
                target_node_cid="target",
                probability_weight=0.5,
                compute_weight_magnitude=1,
                discount_factor=1.0,
                terminal_condition=TerminalConditionContract(),
            )


# ---------------------------------------------------------------------------
# Bulk simple instantiation for broad coverage
# ---------------------------------------------------------------------------


class TestBulkInstantiation:
    """Instantiate models with minimal required fields to exercise init paths."""

    def test_cognitive_agent_node(self) -> None:
        obj = CognitiveAgentNodeProfile(description="test agent")
        assert obj.description == "test agent"

    def test_cognitive_system_node(self) -> None:
        obj = CognitiveSystemNodeProfile(description="test system")
        assert obj.description == "test system"

    def test_cognitive_human_node(self) -> None:
        obj = CognitiveHumanNodeProfile(
            description="test human",
            required_attestation="urn:coreason:email_verified",
        )
        assert obj.topology_class == "human"

    def test_backpressure_policy(self) -> None:
        obj = BackpressurePolicy(max_queue_depth=100)
        assert obj.max_queue_depth == 100

    def test_auction_policy(self) -> None:
        obj = AuctionPolicy(auction_type="sealed_bid", tie_breaker="random", max_bidding_window_ms=5000)
        assert obj.auction_type == "sealed_bid"

    def test_cognitive_format_contract(self) -> None:
        from coreason_manifest.spec.ontology import ConstrainedDecodingPolicy

        policy = ConstrainedDecodingPolicy(compiler_backend="urn:coreason:outlines")
        obj = CognitiveFormatContract(decoding_policy=policy)
        assert obj.require_think_tags is True

    def test_cognitive_sampling_policy(self) -> None:
        obj = CognitiveSamplingPolicy(max_complexity_hops=5)
        assert obj.max_complexity_hops == 5

    def test_cognitive_routing_contract(self) -> None:
        obj = CognitiveRoutingContract(dynamic_top_k=3, routing_temperature=0.7)
        assert obj.dynamic_top_k == 3

    def test_activation_steering(self) -> None:
        obj = ActivationSteeringContract(
            steering_vector_hash="a" * 64,
            injection_layers=[0, 1, 2],
            scaling_factor=1.0,
            vector_modality="additive",
        )
        assert len(obj.injection_layers) == 3

    def test_belief_mutation_event(self) -> None:
        obj = BeliefMutationEvent(
            event_cid="bm-1",
            timestamp=time.time(),
            payload={"key": "value"},
        )
        assert obj.event_cid == "bm-1"

    def test_browser_dom_state(self) -> None:
        obj = BrowserDOMState(
            current_url="https://example.com",
            viewport_size=(1920, 1080),
            dom_hash="d" * 64,
            accessibility_tree_hash="a" * 64,
        )
        assert obj.current_url == "https://example.com"

    def test_circuit_breaker_event(self) -> None:
        obj = CircuitBreakerEvent(
            event_cid="cb-1",
            timestamp=time.time(),
            target_node_cid="did:z:node1",
            error_signature="timeout",
        )
        assert obj.error_signature == "timeout"

    def test_agent_attestation(self) -> None:
        obj = AgentAttestationReceipt(
            training_lineage_hash="a" * 64,
            developer_signature="b" * 64,
            capability_merkle_root="c" * 64,
        )
        assert obj.capability_merkle_root == "c" * 64

    def test_causal_directed_edge(self) -> None:
        from coreason_manifest.spec.ontology import EvidentiaryGroundingSLA

        sla = EvidentiaryGroundingSLA(
            minimum_nli_entailment_score=0.8,
        )
        obj = CausalDirectedEdgeState(
            source_variable="X",
            target_variable="Y",
            edge_class="direct_cause",
            predicate_curie="rdf:causes",
            grounding_sla=sla,
        )
        assert obj.source_variable == "X"

    def test_kinetic_separation(self) -> None:
        obj = KineticSeparationPolicy(
            policy_cid="ks-1",
            mutually_exclusive_clusters=[["tool_a", "tool_b"]],
            enforcement_action="halt_and_quarantine",
        )
        assert len(obj.mutually_exclusive_clusters) == 1

    def test_context_expansion(self) -> None:
        obj = ContextExpansionPolicy(
            expansion_paradigm="sliding_window",
            max_token_budget=4096,
        )
        assert obj.max_token_budget == 4096

    def test_grading_criterion(self) -> None:
        obj = GradingCriterionProfile(
            criterion_cid="gc-1",
            description="test criterion",
            weight=1.0,
        )
        assert obj.weight == 1.0

    def test_active_inference_contract(self) -> None:
        obj = ActiveInferenceContract(
            task_cid="ai-1",
            target_hypothesis_cid="hyp-1",
            target_condition_cid="cond-1",
            selected_tool_name="tool-1",
            expected_information_gain=0.5,
            execution_cost_budget_magnitude=100,
        )
        assert obj.expected_information_gain == 0.5
