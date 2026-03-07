# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.
import re
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.core.primitives import DataClassification, RiskLevel
from coreason_manifest.oversight.dlp import InformationFlowPolicy
from coreason_manifest.oversight.governance import GlobalGovernance
from coreason_manifest.oversight.intervention import (
    AnyInterventionPayload,
    InterventionPolicy,
    InterventionRequest,
    InterventionVerdict,
    OverrideIntent,
)
from coreason_manifest.oversight.resilience import (
    AnyResiliencePayload,
    CircuitBreakerTrip,
    FallbackTrigger,
    QuarantineOrder,
)
from coreason_manifest.presentation.intents import (
    AdjudicationIntent,
    AnyPresentationIntent,
    DraftingIntent,
    EscalationIntent,
    InformationalIntent,
)
from coreason_manifest.presentation.scivis import AnyPanel, GrammarPanel, InsightCard
from coreason_manifest.state.argumentation import ArgumentGraph
from coreason_manifest.state.events import (
    AnyStateEvent,
    BeliefUpdateEvent,
    HypothesisGenerationEvent,
    InterventionalCausalTask,
    ObservationEvent,
    SystemFaultEvent,
)
from coreason_manifest.state.memory import EpistemicLedger
from coreason_manifest.state.semantic import (
    SemanticEdge,
    SemanticNode,
)
from coreason_manifest.telemetry.custody import CustodyRecord
from coreason_manifest.telemetry.schemas import TraceExportBatch
from coreason_manifest.testing.chaos import ChaosExperiment
from coreason_manifest.testing.red_team import AdversarialSimulationProfile
from coreason_manifest.tooling import ActionSpace, ToolDefinition
from coreason_manifest.workflow.auctions import AuctionState, TaskAward
from coreason_manifest.workflow.envelope import WorkflowEnvelope
from coreason_manifest.workflow.nodes import AgentNode, AnyNode, CompositeNode, HumanNode, SystemNode
from coreason_manifest.workflow.topologies import AnyTopology, OntologicalHandshake, StateContract


@st.composite
def draw_did_string(draw: Any) -> str:
    """Generates a valid W3C DID string to satisfy the NodeID regex."""
    method = draw(st.sampled_from(["jwk", "web", "key", "ethr", "peer"]))
    identifier = draw(st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"))
    return f"did:{method}:{identifier}"


@st.composite
def draw_vc_presentation(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "presentation_format": st.sampled_from(["jwt_vc", "ldp_vc", "sd_jwt", "zkp_vc"]),
                "issuer_did": draw_did_string(),
                "cryptographic_proof_blob": st.text(min_size=10),
                "authorization_claims": st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
            }
        )
    )
    return res


@st.composite
def draw_escalation_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "uncertainty_escalation_threshold": st.floats(min_value=0.0, max_value=1.0),
                "max_latent_tokens_budget": st.integers(min_value=1),
                "max_test_time_compute_ms": st.integers(min_value=1),
            }
        )
    )
    return res


@st.composite
def draw_dynamic_convergence_sla(draw: Any) -> dict[str, Any]:
    return draw(
        st.fixed_dictionaries(
            {
                "convergence_delta_epsilon": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "lookback_window_steps": st.integers(min_value=1, max_value=100),
                "minimum_reasoning_steps": st.integers(min_value=1, max_value=100),
            }
        )
    )


@st.composite
def draw_process_reward_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "pruning_threshold": st.floats(min_value=0.0, max_value=1.0),
                "max_backtracks_allowed": st.integers(min_value=0),
                "evaluator_model_name": st.one_of(st.none(), st.text()),
                "convergence_sla": st.one_of(st.none(), draw_dynamic_convergence_sla()),
            }
        )
    )
    return res


@st.composite
def draw_thought_branch(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "branch_id": st.text(min_size=1),
                "parent_branch_id": st.one_of(st.none(), st.text()),
                "latent_content_hash": st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
                "prm_score": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0)),
            }
        )
    )
    return res


@st.composite
def draw_latent_scratchpad_trace(draw: Any) -> dict[str, Any]:
    explored_branches = draw(
        st.lists(draw_thought_branch(), min_size=1, max_size=5, unique_by=lambda b: b["branch_id"])
    )
    explored_branch_ids = [branch["branch_id"] for branch in explored_branches]

    # ensure resolution_branch_id and discarded_branches are valid if generated
    resolution_branch_id = draw(st.one_of(st.none(), st.sampled_from(explored_branch_ids)))
    discarded_branches = draw(st.lists(st.sampled_from(explored_branch_ids), max_size=len(explored_branch_ids)))

    res: dict[str, Any] = {
        "trace_id": draw(st.text(min_size=1)),
        "explored_branches": explored_branches,
        "discarded_branches": discarded_branches,
        "resolution_branch_id": resolution_branch_id,
        "total_latent_tokens": draw(st.integers(min_value=0)),
    }
    return res


@st.composite
def draw_reflex_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "confidence_threshold": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "allowed_read_only_tools": st.lists(st.text(), max_size=100),
            }
        )
    )
    return res


@st.composite
def draw_causal_directed_edge(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "source_variable": st.text(min_size=1),
                "target_variable": st.text(min_size=1),
                "edge_type": st.sampled_from(["direct_cause", "confounder", "collider", "mediator"]),
            }
        )
    )
    return res


@st.composite
def draw_structural_causal_model(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "observed_variables": st.lists(st.text(), max_size=100),
                "latent_variables": st.lists(st.text(), max_size=100),
                "causal_edges": st.lists(draw_causal_directed_edge(), max_size=100),
            }
        )
    )
    return res


@st.composite
def draw_falsification_condition(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "condition_id": st.text(min_size=1),
                "description": st.text(),
                "required_tool_name": st.one_of(st.none(), st.text()),
                "falsifying_observation_signature": st.text(),
            }
        )
    )
    return res


@st.composite
def draw_hypothesis_generation_event(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("hypothesis"),
                "hypothesis_id": st.text(min_size=1),
                "premise_text": st.text(),
                "bayesian_prior": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "falsification_conditions": st.lists(
                    draw_falsification_condition(), min_size=1, max_size=10, unique_by=lambda x: x["condition_id"]
                ),
                "status": st.sampled_from(["active", "falsified", "verified"]),
                "event_id": st.text(min_size=1),
                "timestamp": st.floats(allow_nan=False, allow_infinity=False),
                "causal_model": st.one_of(st.none(), draw_structural_causal_model()),
            }
        )
    )
    return res


@st.composite
def draw_interventional_causal_task(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "task_id": st.text(min_size=1),
                "target_variable": st.text(min_size=1),
                "do_operator_interventions": st.dictionaries(st.text(), st.one_of(st.text(), st.integers())),
                "expected_information_gain": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
            }
        )
    )
    return res


@st.composite
def draw_active_inference_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "task_id": st.text(min_size=1),
                "target_hypothesis_id": st.text(),
                "target_condition_id": st.text(),
                "selected_tool_name": st.text(),
                "expected_information_gain": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "execution_cost_budget_cents": st.integers(min_value=0),
            }
        )
    )
    return res


@st.composite
def draw_activation_steering_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "steering_vector_hash": st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
                "injection_layers": st.lists(st.integers(min_value=0), min_size=1, max_size=10),
                "scaling_factor": st.floats(allow_nan=False, allow_infinity=False),
                "vector_modality": st.sampled_from(["additive", "ablation", "clamping"]),
            }
        )
    )
    return res


@st.composite
def draw_cognitive_routing_directive(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "dynamic_top_k": st.integers(min_value=1, max_value=100),
                "routing_temperature": st.floats(min_value=0.0, allow_nan=False, allow_infinity=False),
                "expert_logit_biases": st.dictionaries(
                    st.text(min_size=1), st.floats(allow_nan=False, allow_infinity=False), max_size=10
                ),
                "enforce_functional_isolation": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_cognitive_state_profile(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "urgency_index": st.floats(min_value=0.0, max_value=1.0),
                "caution_index": st.floats(min_value=0.0, max_value=1.0),
                "divergence_tolerance": st.floats(min_value=0.0, max_value=1.0),
                "activation_steering": st.one_of(st.none(), draw_activation_steering_contract()),
                "moe_routing_directive": st.one_of(st.none(), draw_cognitive_routing_directive()),
            }
        )
    )
    return res


@st.composite
def draw_cognitive_uncertainty_profile(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "aleatoric_entropy": st.floats(min_value=0.0, max_value=1.0),
                "epistemic_uncertainty": st.floats(min_value=0.0, max_value=1.0),
                "semantic_consistency_score": st.floats(min_value=0.0, max_value=1.0),
                "requires_abductive_escalation": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_embodied_sensory_vector(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "sensory_modality": st.sampled_from(["video", "audio", "spatial_telemetry"]),
                "bayesian_surprise_score": st.floats(min_value=0.0),
                "temporal_duration_ms": st.integers(min_value=1, max_value=86400000),
                "salience_threshold_breached": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_epistemic_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "active": st.booleans(),
                "dissonance_threshold": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "action_on_gap": st.sampled_from(["fail", "probe", "clarify"]),
            }
        )
    )
    return res


@st.composite
def draw_correction_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "max_loops": st.integers(min_value=0, max_value=50),
                "rollback_on_failure": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_intervention_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "trigger": st.sampled_from(
                    [
                        "on_start",
                        "on_node_transition",
                        "before_tool_execution",
                        "on_failure",
                        "on_consensus_reached",
                        "on_max_loops_reached",
                    ]
                ),
                "blocking": st.booleans(),
                "scope": st.one_of(
                    st.none(),
                    st.fixed_dictionaries(
                        {
                            "allowed_fields": st.lists(st.text(), max_size=100),
                            "json_schema_whitelist": st.dictionaries(
                                st.text(), st.one_of(st.text(), st.integers(), st.booleans())
                            ),
                        }
                    ),
                ),
            }
        )
    )
    return res


@st.composite
def draw_secure_sub_session(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "session_id": st.text(max_size=255),
                "allowed_vault_keys": st.lists(st.text(), max_size=100),
                "max_ttl_seconds": st.integers(min_value=1, max_value=3600),
                "description": st.text(max_size=2000),
            }
        )
    )
    return res


@st.composite
def draw_agent_attestation(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "training_lineage_hash": st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
                "developer_signature": st.text(min_size=1),
                "capability_merkle_root": st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
                "credential_presentations": st.lists(draw_vc_presentation(), max_size=5),
            }
        )
    )
    return res


@st.composite
def draw_peft_adapter_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "adapter_id": st.text(min_size=1),
                "safetensors_hash": st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
                "base_model_hash": st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
                "adapter_rank": st.integers(min_value=1, max_value=256),
                "target_modules": st.lists(st.text(min_size=1), min_size=1, max_size=10),
                "eviction_ttl_seconds": st.one_of(st.none(), st.integers(min_value=1)),
            }
        )
    )
    return res


@st.composite
def draw_routing_frontier(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "max_latency_ms": st.integers(min_value=1),
                "max_cost_microcents_per_token": st.integers(min_value=1),
                "min_capability_score": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "tradeoff_preference": st.sampled_from(
                    ["latency_optimized", "cost_optimized", "capability_optimized", "carbon_optimized", "balanced"]
                ),
                "max_carbon_intensity_gco2eq_kwh": st.one_of(
                    st.none(), st.floats(min_value=0.0, allow_nan=False, allow_infinity=False)
                ),
            }
        )
    )
    return res


@st.composite
def draw_agent_node_payload(draw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "agent", "description": draw(st.text())}
    if draw(st.booleans()):
        payload["compute_frontier"] = draw(draw_routing_frontier())
    if draw(st.booleans()):
        payload["peft_adapters"] = draw(st.lists(draw_peft_adapter_contract(), max_size=5))
    if draw(st.booleans()):
        payload["agent_attestation"] = draw(draw_agent_attestation())
    if draw(st.booleans()):
        payload["intervention_policies"] = draw(st.lists(draw_intervention_policy(), max_size=100))
    if draw(st.booleans()):
        payload["action_space_id"] = draw(draw_did_string())
    if draw(st.booleans()):
        payload["secure_sub_session"] = draw(draw_secure_sub_session())
    if draw(st.booleans()):
        payload["reflex_policy"] = draw(draw_reflex_policy())
    if draw(st.booleans()):
        payload["epistemic_policy"] = draw(draw_epistemic_policy())
    if draw(st.booleans()):
        payload["correction_policy"] = draw(draw_correction_policy())
    return payload


@st.composite
def draw_human_node_payload(draw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "human", "description": draw(st.text())}
    if draw(st.booleans()):
        payload["intervention_policies"] = draw(st.lists(draw_intervention_policy(), max_size=100))
    return payload


@st.composite
def draw_system_node_payload(draw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "system", "description": draw(st.text())}
    if draw(st.booleans()):
        payload["intervention_policies"] = draw(st.lists(draw_intervention_policy(), max_size=100))
    return payload


def draw_base_node_payload() -> st.SearchStrategy[dict[str, Any]]:
    return st.one_of(draw_agent_node_payload(), draw_human_node_payload(), draw_system_node_payload())


@st.composite
def draw_input_mapping(draw: Any) -> dict[str, Any]:
    return {"parent_key": draw(st.text()), "child_key": draw(st.text())}


@st.composite
def draw_output_mapping(draw: Any) -> dict[str, Any]:
    return {"child_key": draw(st.text()), "parent_key": draw(st.text())}


@st.composite
def draw_dimensional_projection_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "source_dimensionality": st.integers(min_value=1),
                "target_dimensionality": st.integers(min_value=1),
                "isometry_preservation_score": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "projection_matrix_hash": st.text(min_size=10),
            }
        )
    )
    return res


@st.composite
def draw_ontological_handshake(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "initiating_node_id": draw_did_string(),
                "receiving_node_id": draw_did_string(),
                "latent_vector_similarity": st.floats(
                    min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "projection_contract": st.one_of(st.none(), draw_dimensional_projection_contract()),
            }
        )
    )
    return res


@st.composite
def draw_ontological_alignment_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "min_cosine_similarity": st.floats(
                    min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "require_isometry_proof": st.booleans(),
                "fallback_state_contract": st.none(),
            }
        )
    )
    return res


@st.composite
def draw_prediction_market_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "staking_function": st.sampled_from(["linear", "quadratic"]),
                "min_liquidity_cents": st.integers(min_value=0),
                "convergence_delta_threshold": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
            }
        )
    )
    return res


@st.composite
def draw_consensus_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "strategy": st.sampled_from(["unanimous", "majority", "debate_rounds", "prediction_market"]),
                "tie_breaker_node_id": st.one_of(
                    st.none(),
                    draw_did_string(),
                ),
                "max_debate_rounds": st.one_of(st.none(), st.integers(min_value=1, max_value=100)),
                "prediction_market_rules": st.one_of(st.none(), draw_prediction_market_policy()),
            }
        )
    )
    return res


@st.composite
def draw_hypothesis_stake(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "agent_id": draw_did_string(),
                "target_hypothesis_id": st.text(min_size=1),
                "staked_cents": st.integers(min_value=1),
                "implied_probability": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            }
        )
    )
    return res


@st.composite
def draw_prediction_market_state(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "market_id": st.text(min_size=1),
                "resolution_oracle_condition_id": st.text(),
                "lmsr_b_parameter": st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
                "order_book": st.lists(draw_hypothesis_stake(), max_size=10),
                "current_market_probabilities": st.dictionaries(st.text(), st.floats(), max_size=10),
            }
        )
    )
    return res


@st.composite
def draw_market_resolution(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "market_id": st.text(min_size=1),
                "winning_hypothesis_id": st.text(),
                "falsified_hypothesis_ids": st.lists(st.text(), max_size=10),
                "payout_distribution": st.dictionaries(st.text(), st.integers(), max_size=10),
            }
        )
    )
    return res


@st.composite
def draw_backpressure_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "max_queue_depth": st.integers(min_value=1),
                "token_budget_per_branch": st.one_of(st.none(), st.integers(min_value=1)),
                "max_tokens_per_minute": st.one_of(st.none(), st.integers(min_value=1)),
                "max_requests_per_minute": st.one_of(st.none(), st.integers(min_value=1)),
                "max_uninterruptible_span_ms": st.one_of(st.none(), st.integers(min_value=1)),
            }
        )
    )
    return res


def draw_topology_payload(nodes_strategy: st.SearchStrategy[dict[str, Any]]) -> st.SearchStrategy[dict[str, Any]]:
    dag_strategy = st.fixed_dictionaries(
        {
            "type": st.just("dag"),
            "nodes": st.dictionaries(
                draw_did_string(),
                nodes_strategy,
                max_size=5,
            ),
            "shared_state_contract": st.none(),
            "information_flow": st.none(),
            "observability": st.none(),
            "edges": st.just([]),
            "allow_cycles": st.booleans(),
            "backpressure": st.one_of(st.none(), draw_backpressure_policy()),
        }
    )

    # To satisfy the model_validator `check_adjudicator_id` in `CouncilTopology`,
    # `adjudicator_id` MUST be present in `nodes`.
    # Let's write a small map strategy to ensure `adjudicator_id` is a key in `nodes`.
    def _council_mapper(payload: dict[str, Any]) -> dict[str, Any]:
        if not payload["nodes"]:
            return payload
        # Pick the first node ID as the adjudicator_id
        payload["adjudicator_id"] = next(iter(payload["nodes"].keys()))
        return payload

    council_strategy = st.fixed_dictionaries(
        {
            "type": st.just("council"),
            "nodes": st.dictionaries(
                draw_did_string(),
                nodes_strategy,
                min_size=1,
                max_size=5,
            ),
            "shared_state_contract": st.none(),
            "information_flow": st.none(),
            "observability": st.none(),
            "adjudicator_id": st.text(
                min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            ),
            "diversity_policy": st.none(),
            "consensus_policy": st.one_of(st.none(), draw_consensus_policy()),
            "ontological_alignment": st.one_of(st.none(), draw_ontological_alignment_policy()),
        }
    ).map(_council_mapper)

    swarm_strategy = st.fixed_dictionaries(
        {
            "type": st.just("swarm"),
            "nodes": st.dictionaries(
                draw_did_string(),
                nodes_strategy,
                max_size=5,
            ),
            "shared_state_contract": st.none(),
            "information_flow": st.none(),
            "observability": st.none(),
            "spawning_threshold": st.integers(min_value=1, max_value=10),
            "max_concurrent_agents": st.integers(min_value=10, max_value=100),
            "auction_policy": st.none(),
            "active_prediction_markets": st.lists(draw_prediction_market_state(), max_size=10),
            "resolved_markets": st.lists(draw_market_resolution(), max_size=10),
        }
    )

    smpc_strategy = st.fixed_dictionaries(
        {
            "type": st.just("smpc"),
            "nodes": st.dictionaries(
                draw_did_string(),
                nodes_strategy,
                min_size=2,
                max_size=5,
            ),
            "shared_state_contract": st.none(),
            "information_flow": st.none(),
            "observability": st.none(),
            "smpc_protocol": st.sampled_from(["garbled_circuits", "secret_sharing", "oblivious_transfer"]),
            "joint_function_uri": st.text(min_size=1),
            "participant_node_ids": st.lists(
                draw_did_string(),
                min_size=2,
                max_size=5,
            ),
            "ontological_alignment": st.one_of(st.none(), draw_ontological_alignment_policy()),
        }
    )

    return st.one_of(dag_strategy, council_strategy, swarm_strategy, smpc_strategy)


def draw_composite_node_payload(
    topology_strategy: st.SearchStrategy[dict[str, Any]],
) -> st.SearchStrategy[dict[str, Any]]:
    return st.fixed_dictionaries(
        {
            "type": st.just("composite"),
            "description": st.text(),
            "intervention_policies": st.lists(draw_intervention_policy(), max_size=10),
            "topology": topology_strategy,
            "input_mappings": st.lists(draw_input_mapping(), max_size=5),
            "output_mappings": st.lists(draw_output_mapping(), max_size=5),
        }
    )


def draw_any_node_recursive() -> st.SearchStrategy[dict[str, Any]]:
    def extend_node(node_strategy: st.SearchStrategy[dict[str, Any]]) -> st.SearchStrategy[dict[str, Any]]:
        # Combining topologies recursively:
        topologies = draw_topology_payload(node_strategy)
        return st.one_of(node_strategy, draw_composite_node_payload(topologies))

    base_nodes = draw_base_node_payload()
    return st.recursive(base_nodes, extend_node, max_leaves=3)


node_adapter: TypeAdapter[AnyNode] = TypeAdapter(AnyNode)
chaos_adapter: TypeAdapter[ChaosExperiment] = TypeAdapter(ChaosExperiment)
action_space_adapter: TypeAdapter[ActionSpace] = TypeAdapter(ActionSpace)
tool_definition_adapter: TypeAdapter[ToolDefinition] = TypeAdapter(ToolDefinition)
event_adapter: TypeAdapter[AnyStateEvent] = TypeAdapter(AnyStateEvent)
panel_adapter: TypeAdapter[AnyPanel] = TypeAdapter(AnyPanel)
resilience_adapter: TypeAdapter[AnyResiliencePayload] = TypeAdapter(AnyResiliencePayload)
global_governance_adapter: TypeAdapter[GlobalGovernance] = TypeAdapter(GlobalGovernance)
state_contract_adapter: TypeAdapter[StateContract] = TypeAdapter(StateContract)
intervention_policy_adapter: TypeAdapter[InterventionPolicy] = TypeAdapter(InterventionPolicy)


@given(draw_any_node_recursive())
def test_anynode_routing(payload: dict[str, Any]) -> None:
    parsed = node_adapter.validate_python(payload)
    node_type = payload["type"]
    if node_type == "agent":
        assert isinstance(parsed, AgentNode)
    elif node_type == "human":
        assert isinstance(parsed, HumanNode)
    elif node_type == "system":
        assert isinstance(parsed, SystemNode)
    elif node_type == "composite":
        assert isinstance(parsed, CompositeNode)


@given(st.text())
def test_anynode_invalid(invalid_type: str) -> None:
    if invalid_type in ["agent", "human", "system", "composite"]:
        return
    payload = {"type": invalid_type, "description": "test"}
    with pytest.raises(ValidationError):
        node_adapter.validate_python(payload)


@st.composite
def draw_distribution_profile(draw: Any) -> dict[str, Any]:
    distribution_type = draw(st.sampled_from(["gaussian", "uniform", "beta"]))
    mean = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))
    variance = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))
    confidence_interval_95 = draw(
        st.one_of(
            st.none(),
            st.tuples(
                st.floats(allow_nan=False, allow_infinity=False),
                st.floats(allow_nan=False, allow_infinity=False),
            ),
        )
    )

    if confidence_interval_95 is not None and confidence_interval_95[0] >= confidence_interval_95[1]:
        confidence_interval_95 = (confidence_interval_95[1], confidence_interval_95[0])
        if confidence_interval_95[0] >= confidence_interval_95[1]:
            # If they are exactly equal after swap, adjust one.
            confidence_interval_95 = (confidence_interval_95[0], confidence_interval_95[1] + 1.0)

    res: dict[str, Any] = {
        "distribution_type": distribution_type,
        "mean": mean,
        "variance": variance,
        "confidence_interval_95": confidence_interval_95,
    }
    return res


@st.composite
def draw_fitness_objective(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "target_metric": st.text(min_size=1),
                "direction": st.sampled_from(["maximize", "minimize"]),
                "weight": st.floats(allow_nan=False, allow_infinity=False),
            }
        )
    )
    return res


@st.composite
def draw_verifiable_entropy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "vrf_proof": st.text(min_size=10),
                "public_key": st.text(min_size=10),
                "seed_hash": st.text(min_size=10),
            }
        )
    )
    return res


@st.composite
def draw_mutation_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "mutation_rate": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "temperature_shift_variance": st.floats(allow_nan=False, allow_infinity=False),
                "verifiable_entropy": st.one_of(st.none(), draw_verifiable_entropy()),
            }
        )
    )
    return res


@st.composite
def draw_crossover_strategy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "strategy_type": st.sampled_from(["uniform_blend", "single_point", "heuristic"]),
                "blending_factor": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "verifiable_entropy": st.one_of(st.none(), draw_verifiable_entropy()),
            }
        )
    )
    return res


@st.composite
def draw_observability_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "traces_sampled": st.booleans(),
                "detailed_events": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_evolutionary_topology_payload(draw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("evolutionary"),
                "nodes": st.just({}),  # For simplicity, empty nodes
                "shared_state_contract": st.none(),
                "information_flow": st.none(),
                "observability": st.one_of(st.none(), draw_observability_policy()),
                "generations": st.integers(min_value=1),
                "population_size": st.integers(min_value=1),
                "mutation": draw_mutation_policy(),
                "crossover": draw_crossover_strategy(),
                "fitness_objectives": st.lists(draw_fitness_objective(), min_size=1),
            }
        )
    )
    return payload


topology_adapter: TypeAdapter[AnyTopology] = TypeAdapter(AnyTopology)


@given(draw_evolutionary_topology_payload())
def test_anytopology_routing(payload: dict[str, Any]) -> None:
    parsed = topology_adapter.validate_python(payload)
    assert parsed.type == "evolutionary"


@st.composite
def draw_causal_attribution(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "source_event_id": st.text(min_size=1),
                "influence_weight": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            }
        )
    )
    return res


@st.composite
def draw_zkp(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "proof_protocol": st.sampled_from(["zk-SNARK", "zk-STARK", "plonk", "bulletproofs"]),
                "public_inputs_hash": st.text(min_size=1),
                "verifier_key_id": st.text(min_size=1),
                "cryptographic_blob": st.text(min_size=10),
                "latent_state_commitments": st.dictionaries(st.text(), st.text()),
            }
        )
    )
    return res


@st.composite
def draw_sae_feature_activation(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "feature_index": st.integers(min_value=0),
                "activation_magnitude": st.floats(allow_nan=False, allow_infinity=False),
                "interpretability_label": st.one_of(st.none(), st.text()),
            }
        )
    )
    return res


@st.composite
def draw_neural_audit_attestation(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "audit_id": st.text(min_size=1),
                "layer_activations": st.dictionaries(
                    st.integers(),
                    st.lists(draw_sae_feature_activation(), max_size=10),
                ),
                "causal_scrubbing_applied": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_mechanistic_audit_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "trigger_conditions": st.lists(
                    st.sampled_from(["on_tool_call", "on_belief_update", "on_quarantine", "on_falsification"]),
                    min_size=1,
                    max_size=4,
                    unique=True,
                ),
                "target_layers": st.lists(st.integers(), min_size=1, max_size=10),
                "max_features_per_layer": st.integers(min_value=1),
                "require_zk_commitments": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_hardware_attestation(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "enclave_type": st.sampled_from(["intel_tdx", "amd_sev_snp", "aws_nitro", "nvidia_cc"]),
                "platform_measurement_hash": st.text(min_size=10),
                "hardware_signature_blob": st.text(min_size=20),
            }
        )
    )
    return res


@st.composite
def draw_browser_dom_state(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("browser"),
                "current_url": st.text(min_size=1),
                "viewport_size": st.tuples(st.integers(min_value=1), st.integers(min_value=1)),
                "dom_hash": st.text(min_size=10),
                "accessibility_tree_hash": st.text(min_size=10),
                "screenshot_cid": st.one_of(st.none(), st.text(min_size=10)),
            }
        )
    )
    return res


@st.composite
def draw_terminal_buffer_state(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("terminal"),
                "working_directory": st.text(min_size=1),
                "stdout_hash": st.text(min_size=10),
                "stderr_hash": st.text(min_size=10),
                "env_variables_hash": st.text(min_size=10),
            }
        )
    )
    return res


def draw_any_toolchain_state() -> st.SearchStrategy[dict[str, Any]]:
    return st.one_of(draw_browser_dom_state(), draw_terminal_buffer_state())


@st.composite
def draw_barge_in_interrupt_event(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("barge_in"),
                "event_id": st.text(min_size=1),
                "timestamp": st.floats(allow_nan=False, allow_infinity=False),
                "target_event_id": st.text(min_size=1),
                "sensory_trigger": st.one_of(st.none(), draw_embodied_sensory_vector()),
                "retained_partial_payload": st.one_of(st.none(), st.text(), st.dictionaries(st.text(), st.text())),
                "epistemic_disposition": st.sampled_from(["discard", "retain_as_context", "mark_as_falsified"]),
            }
        )
    )
    return res


@st.composite
def _local_draw_any_state_event(draw: Any) -> dict[str, Any]:
    event_type = draw(st.sampled_from(["observation", "belief_update", "system_fault", "hypothesis", "barge_in"]))

    if event_type == "barge_in":
        barge_in_res: dict[str, Any] = draw(draw_barge_in_interrupt_event())
        return barge_in_res

    if event_type == "hypothesis":
        res: dict[str, Any] = draw(draw_hypothesis_generation_event())
        return res

    payload: dict[str, Any] = {
        "type": event_type,
        "event_id": draw(st.text()),
        "timestamp": draw(st.floats(allow_nan=False, allow_infinity=False)),
    }
    if event_type in ("observation", "belief_update"):
        payload["payload"] = draw(
            st.dictionaries(
                st.text(),
                st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.booleans()),
                max_size=5,
            )
        )
        payload["source_node_id"] = draw(
            st.one_of(
                st.none(),
                draw_did_string(),
            )
        )
        if event_type == "belief_update":
            payload["causal_attributions"] = draw(st.lists(draw_causal_attribution(), max_size=10))
        if draw(st.booleans()):
            payload["zk_proof"] = draw(draw_zkp())
        if draw(st.booleans()):
            payload["hardware_attestation"] = draw(draw_hardware_attestation())
        if event_type == "observation" and draw(st.booleans()):
            payload["toolchain_snapshot"] = draw(draw_any_toolchain_state())
        if event_type == "observation" and draw(st.booleans()):
            payload["sensory_trigger"] = draw(draw_embodied_sensory_vector())
        if event_type == "belief_update" and draw(st.booleans()):
            payload["uncertainty_profile"] = draw(draw_cognitive_uncertainty_profile())
        if event_type == "belief_update" and draw(st.booleans()):
            payload["scratchpad_trace"] = draw(draw_latent_scratchpad_trace())
        if event_type in ("observation", "belief_update") and draw(st.booleans()):
            payload["neural_audit"] = draw(draw_neural_audit_attestation())
    return payload


@given(_local_draw_any_state_event())
def test_anystateevent_routing(payload: dict[str, Any]) -> None:
    parsed = event_adapter.validate_python(payload)
    event_type = payload["type"]
    if event_type == "observation":
        assert isinstance(parsed, ObservationEvent)
    elif event_type == "belief_update":
        assert isinstance(parsed, BeliefUpdateEvent)
    elif event_type == "system_fault":
        assert isinstance(parsed, SystemFaultEvent)
    elif event_type == "hypothesis":
        assert isinstance(parsed, HypothesisGenerationEvent)
    elif event_type == "barge_in":
        from coreason_manifest.state.events import BargeInInterruptEvent

        assert isinstance(parsed, BargeInInterruptEvent)


@given(st.text())
def test_anystateevent_invalid(invalid_type: str) -> None:
    if invalid_type in ["observation", "belief_update", "system_fault", "hypothesis", "barge_in"]:
        return
    payload = {"type": invalid_type, "event_id": "test", "timestamp": 123.0}
    with pytest.raises(ValidationError):
        event_adapter.validate_python(payload)


@st.composite
def draw_scale_definition(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.sampled_from(["linear", "log", "time", "ordinal", "nominal"]),
                "domain_min": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                "domain_max": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
            }
        )
    )
    return res


@st.composite
def draw_channel_encoding(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "channel": st.sampled_from(["x", "y", "color", "size", "opacity", "shape", "text"]),
                "field": st.text(),
                "scale": st.one_of(st.none(), draw_scale_definition()),
            }
        )
    )
    return res


@st.composite
def draw_facet_matrix(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "row_field": st.one_of(st.none(), st.text()),
                "column_field": st.one_of(st.none(), st.text()),
            }
        )
    )
    return res


@st.composite
def draw_grammar_panel_payload(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "panel_id": st.text(),
                "type": st.just("grammar"),
                "title": st.text(),
                "data_source_id": st.text(),
                "mark": st.sampled_from(["point", "line", "area", "bar", "rect", "arc"]),
                "encodings": st.lists(draw_channel_encoding(), max_size=100),
                "facet": st.one_of(st.none(), draw_facet_matrix()),
            }
        )
    )
    return res


@given(st.one_of(draw_grammar_panel_payload()))
def test_grammar_panel_routing(payload: dict[str, Any]) -> None:
    parsed = panel_adapter.validate_python(payload)
    assert isinstance(parsed, GrammarPanel)


@given(
    st.text(),
    st.text().filter(
        lambda x: not bool(re.search(r"<[^=\s\d]", x)) and not bool(re.search(r"on[a-zA-Z]+\s*=", x.lower()))
    ),
)
def test_anypanel_insight(title: str, content: str) -> None:
    payload = {"panel_id": "p3", "type": "insight_card", "title": title, "markdown_content": content}
    parsed = panel_adapter.validate_python(payload)
    assert isinstance(parsed, InsightCard)


@given(
    st.sampled_from(["quarantine", "circuit_breaker", "fallback"]),
    draw_did_string(),
    draw_did_string(),
    st.text(),
)
def test_anyresilience_routing(res_type: str, target: str, fallback: str, reason: str) -> None:
    payload: dict[str, Any] = {"type": res_type, "target_node_id": target}
    if res_type == "quarantine":
        payload["reason"] = reason
    elif res_type == "circuit_breaker":
        payload["error_signature"] = reason
    elif res_type == "fallback":
        payload["fallback_node_id"] = fallback

    parsed = resilience_adapter.validate_python(payload)
    if res_type == "quarantine":
        assert isinstance(parsed, QuarantineOrder)
    elif res_type == "circuit_breaker":
        assert isinstance(parsed, CircuitBreakerTrip)
    elif res_type == "fallback":
        assert isinstance(parsed, FallbackTrigger)


@given(
    st.text(),
    st.floats(min_value=0.0, allow_nan=False, allow_infinity=False),
    st.integers(),
    st.one_of(st.none(), st.lists(st.text(), max_size=100)),
    st.lists(
        st.fixed_dictionaries(
            {
                "fault_type": st.sampled_from(
                    [
                        "context_overload",
                        "incorrect_context",
                        "format_corruption",
                        "latency_spike",
                        "token_throttle",
                        "network_degradation",
                        "temporal_dilation",
                        "dependency_blackout",
                    ]
                ),
                "target_node_id": st.one_of(st.none(), draw_did_string()),
                "intensity": st.floats(allow_nan=False, allow_infinity=False),
            }
        )
    ),
)
def test_chaosexperiment_fuzzing(
    experiment_id: str,
    expected_max_latency: float,
    max_loops_allowed: int,
    required_tool_usage: list[str] | None,
    faults: list[dict[str, Any]],
) -> None:
    payload: dict[str, Any] = {
        "experiment_id": experiment_id,
        "hypothesis": {
            "expected_max_latency": expected_max_latency,
            "max_loops_allowed": max_loops_allowed,
        },
        "faults": faults,
    }
    if required_tool_usage is not None:
        payload["hypothesis"]["required_tool_usage"] = required_tool_usage

    parsed = chaos_adapter.validate_python(payload)
    assert isinstance(parsed, ChaosExperiment)
    assert parsed.experiment_id == experiment_id


@st.composite
def draw_lineage_watermark(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "watermark_protocol": st.sampled_from(["merkle_dag", "statistical_token", "homomorphic_mac"]),
                "hop_signatures": st.dictionaries(
                    draw_did_string(),
                    st.text(min_size=10),
                    max_size=5,
                ),
                "tamper_evident_root": st.text(min_size=10),
            }
        )
    )
    return res


@st.composite
def draw_mcp_capability_whitelist(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "allowed_tools": st.lists(st.text(), max_size=100),
                "allowed_resources": st.lists(st.text(), max_size=100),
                "allowed_prompts": st.lists(st.text(), max_size=100),
            }
        )
    )
    return res


@st.composite
def draw_mcp_server_manifest(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "server_uri": st.text(min_size=1),
                "transport_type": st.sampled_from(["stdio", "sse", "http"]),
                "binary_hash": st.one_of(st.none(), st.text(min_size=10)),
                "capability_whitelist": draw_mcp_capability_whitelist(),
            }
        )
    )
    return res


@given(
    st.fixed_dictionaries(
        {
            "action_space_id": st.text(
                min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            ),
            "native_tools": st.lists(
                st.fixed_dictionaries(
                    {
                        "tool_name": st.text(
                            min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                        ),
                        "description": st.text(),
                        "input_schema": st.dictionaries(st.text(), st.one_of(st.text(), st.integers())),
                        "side_effects": st.fixed_dictionaries(
                            {
                                "is_idempotent": st.booleans(),
                                "mutates_state": st.booleans(),
                            }
                        ),
                        "permissions": st.fixed_dictionaries(
                            {
                                "network_access": st.booleans(),
                                "allowed_domains": st.one_of(st.none(), st.lists(st.text(), max_size=100)),
                                "file_system_read_only": st.booleans(),
                                "auth_requirements": st.one_of(st.none(), st.lists(st.text(), max_size=100)),
                            }
                        ),
                        "sla": st.one_of(
                            st.none(),
                            st.fixed_dictionaries(
                                {
                                    "max_execution_time_ms": st.integers(min_value=1, max_value=2**63 - 1),
                                    "max_memory_mb": st.one_of(
                                        st.none(), st.integers(min_value=1, max_value=2**63 - 1)
                                    ),
                                }
                            ),
                        ),
                        "is_preemptible": st.booleans(),
                    }
                ),
                unique_by=lambda t: t["tool_name"] if isinstance(t, dict) and "tool_name" in t else str(t),
            ),
            "mcp_servers": st.lists(draw_mcp_server_manifest(), max_size=10),
        }
    )
)
def test_actionspace_fuzzing(payload: dict[str, Any]) -> None:
    parsed = action_space_adapter.validate_python(payload)
    assert isinstance(parsed, ActionSpace)
    assert parsed.action_space_id == payload["action_space_id"]


semantic_node_adapter: TypeAdapter[SemanticNode] = TypeAdapter(SemanticNode)
semantic_edge_adapter: TypeAdapter[SemanticEdge] = TypeAdapter(SemanticEdge)


@st.composite
def draw_vector_embedding(draw: Any) -> dict[str, Any]:
    vec = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False), max_size=100))
    res: dict[str, Any] = {
        "vector": vec,
        "dimensionality": len(vec),
        "model_name": draw(st.text()),
    }
    return res


@st.composite
def draw_spatial_anchor(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "page_number": st.one_of(st.none(), st.integers()),
                "bounding_box": st.one_of(
                    st.none(),
                    st.tuples(
                        st.floats(allow_nan=False, allow_infinity=False),
                        st.floats(allow_nan=False, allow_infinity=False),
                        st.floats(allow_nan=False, allow_infinity=False),
                        st.floats(allow_nan=False, allow_infinity=False),
                    ),
                ),
                "block_type": st.one_of(
                    st.none(),
                    st.sampled_from(["paragraph", "table", "figure", "footnote", "header"]),
                ),
            }
        )
    )
    return res


@st.composite
def draw_temporal_bounds(draw: Any) -> dict[str, Any]:
    valid_from = draw(st.one_of(st.none(), st.floats(min_value=0.0, allow_nan=False, allow_infinity=False)))
    valid_to = None
    if valid_from is not None:
        delta = draw(st.floats(min_value=0.0, allow_nan=False, allow_infinity=False))
        valid_to = valid_from + delta
    else:
        valid_to = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))

    return {
        "valid_from": valid_from,
        "valid_to": valid_to,
        "interval_type": draw(
            st.one_of(
                st.none(),
                st.sampled_from(["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]),
            )
        ),
    }


@st.composite
def draw_fhe_profile(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "fhe_scheme": st.sampled_from(["ckks", "bgv", "bfv", "tfhe"]),
                "public_key_id": st.text(min_size=1),
                "ciphertext_blob": st.text(min_size=10),
            }
        )
    )
    return res


@given(
    st.fixed_dictionaries(
        {
            "node_id": st.text(),
            "label": st.text(),
            "text_chunk": st.text(),
            "embedding": st.one_of(st.none(), draw_vector_embedding()),
            "scope": st.sampled_from(["global", "tenant", "session"]),
            "provenance": st.fixed_dictionaries(
                {
                    "extracted_by": draw_did_string(),
                    "source_event_id": st.text(),
                    "spatial_anchor": st.one_of(st.none(), draw_spatial_anchor()),
                    "lineage_watermark": st.one_of(st.none(), draw_lineage_watermark()),
                }
            ),
            "tier": st.sampled_from(["working", "episodic", "semantic"]),
            "temporal_bounds": st.one_of(st.none(), draw_temporal_bounds()),
            "salience": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "baseline_importance": st.floats(allow_nan=False, allow_infinity=False),
                        "decay_rate": st.floats(allow_nan=False, allow_infinity=False),
                    }
                ),
            ),
            "fhe_profile": st.one_of(st.none(), draw_fhe_profile()),
        }
    )
)
def test_semanticnode_fuzzing(payload: dict[str, Any]) -> None:
    parsed = semantic_node_adapter.validate_python(payload)
    assert isinstance(parsed, SemanticNode)
    assert parsed.node_id == payload["node_id"]


@given(
    st.fixed_dictionaries(
        {
            "edge_id": st.text(),
            "subject_node_id": st.text(),
            "object_node_id": st.text(),
            "confidence_score": st.one_of(
                st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
            ),
            "predicate": st.text(),
            "embedding": st.one_of(st.none(), draw_vector_embedding()),
            "provenance": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "extracted_by": draw_did_string(),
                        "source_event_id": st.text(),
                        "lineage_watermark": st.one_of(st.none(), draw_lineage_watermark()),
                    }
                ),
            ),
            "temporal_bounds": st.one_of(st.none(), draw_temporal_bounds()),
            "causal_relationship": st.sampled_from(["causes", "confounds", "correlates_with", "undirected"]),
        }
    )
)
def test_semanticedge_fuzzing(payload: dict[str, Any]) -> None:
    parsed = semantic_edge_adapter.validate_python(payload)
    assert isinstance(parsed, SemanticEdge)
    assert parsed.edge_id == payload["edge_id"]


@st.composite
def draw_formal_verification_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "proof_system": st.sampled_from(["tla_plus", "lean4", "coq", "z3"]),
                "invariant_theorem": st.text(min_size=1),
                "compiled_proof_hash": st.text(min_size=10),
            }
        )
    )
    return res


@given(
    st.fixed_dictionaries(
        {
            "max_budget_cents": st.integers(min_value=0),
            "max_global_tokens": st.integers(),
            "global_timeout_seconds": st.integers(min_value=0),
            "formal_verification": st.one_of(st.none(), draw_formal_verification_contract()),
            "max_carbon_budget_gco2eq": st.one_of(
                st.none(), st.floats(min_value=0.0, allow_nan=False, allow_infinity=False)
            ),
        }
    )
)
def test_global_governance_fuzzing(payload: dict[str, Any]) -> None:
    parsed = global_governance_adapter.validate_python(payload)
    assert isinstance(parsed, GlobalGovernance)
    assert parsed.max_budget_cents == payload["max_budget_cents"]


@given(
    st.fixed_dictionaries(
        {
            "schema_definition": st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
            "strict_validation": st.booleans(),
        }
    )
)
def test_state_contract_fuzzing(payload: dict[str, Any]) -> None:
    parsed = state_contract_adapter.validate_python(payload)
    assert isinstance(parsed, StateContract)
    assert parsed.strict_validation == payload["strict_validation"]


@st.composite
def draw_evidentiary_warrant(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "source_event_id": st.one_of(st.none(), st.text()),
                "source_semantic_node_id": st.one_of(st.none(), st.text()),
                "justification": st.text(),
            }
        )
    )
    return res


@st.composite
def draw_argument_claim(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "claim_id": st.text(),
                "proponent_id": st.text(),
                "text_chunk": st.text(),
                "warrants": st.lists(draw_evidentiary_warrant(), max_size=100),
            }
        )
    )
    return res


@st.composite
def draw_defeasible_attack(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "attack_id": st.text(),
                "source_claim_id": st.text(),
                "target_claim_id": st.text(),
                "attack_vector": st.sampled_from(["rebuttal", "undercutter", "underminer"]),
            }
        )
    )
    return res


@st.composite
def draw_argument_graph(draw: Any) -> dict[str, Any]:
    claims = draw(st.lists(draw_argument_claim(), max_size=100))
    claims_dict = {claim["claim_id"]: claim for claim in claims}

    attacks = draw(st.lists(draw_defeasible_attack(), max_size=100))
    attacks_dict = {attack["attack_id"]: attack for attack in attacks}

    res: dict[str, Any] = {"claims": claims_dict, "attacks": attacks_dict}
    return res


argument_graph_adapter: TypeAdapter[ArgumentGraph] = TypeAdapter(ArgumentGraph)


@given(draw_argument_graph())
def test_argument_graph_fuzzing(payload: dict[str, Any]) -> None:
    parsed = argument_graph_adapter.validate_python(payload)
    assert isinstance(parsed, ArgumentGraph)


@st.composite
def draw_task_announcement(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "task_id": st.text(),
                "required_action_space_id": st.one_of(
                    st.none(),
                    draw_did_string(),
                ),
                "max_budget_cents": st.integers(min_value=0),
            }
        )
    )
    return res


@st.composite
def draw_agent_bid(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "agent_id": draw_did_string(),
                "estimated_cost_cents": st.integers(min_value=0),
                "estimated_latency_ms": st.integers(min_value=0),
                "estimated_carbon_gco2eq": st.floats(min_value=0.0, allow_nan=False, allow_infinity=False),
                "confidence_score": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            }
        )
    )
    return res


@st.composite
def draw_escrow_policy(draw: Any, max_escrow: int) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "escrow_locked_cents": st.integers(min_value=0, max_value=max_escrow),
                "release_condition_metric": st.text(min_size=1),
                "refund_target_node_id": st.text(
                    min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                ),
            }
        )
    )
    return res


@st.composite
def draw_task_award(draw: Any) -> dict[str, Any]:
    price = draw(st.integers(min_value=0))
    # Allocate 100% of the price to a single generated agent ID to satisfy zero-sum rules
    agent_id = draw(draw_did_string())

    award: dict[str, Any] = {
        "task_id": draw(st.text()),
        "awarded_syndicate": {agent_id: price},
        "cleared_price_cents": price,
    }

    if draw(st.booleans()):
        # CRITICAL: Pass the generated price to bound the escrow generation
        award["escrow"] = draw(draw_escrow_policy(max_escrow=price))

    return award


@st.composite
def draw_auction_state(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "announcement": draw_task_announcement(),
                "bids": st.lists(draw_agent_bid(), max_size=100),
                "award": st.one_of(st.none(), draw_task_award()),
            }
        )
    )
    return res


auction_state_adapter: TypeAdapter[AuctionState] = TypeAdapter(AuctionState)


@given(draw_auction_state())
def test_auction_state_fuzzing(payload: dict[str, Any]) -> None:
    parsed = auction_state_adapter.validate_python(payload)
    assert isinstance(parsed, AuctionState)


def test_task_award_syndicate_invalid() -> None:
    payload = {
        "task_id": "test_task",
        "awarded_syndicate": {"agent_1": 50, "agent_2": 40},
        "cleared_price_cents": 100,
    }
    with pytest.raises(ValueError, match="Syndicate allocation sum must exactly equal cleared_price_cents"):
        TypeAdapter(TaskAward).validate_python(payload)


@st.composite
def draw_redaction_rule(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "rule_id": st.text(),
                "classification": st.sampled_from(["phi", "pii", "pci", "confidential", "public"]),
                "target_pattern": st.text(),
                "target_regex_pattern": st.text(max_size=200),
                "context_exclusion_zones": st.one_of(st.none(), st.lists(st.text(), max_size=100)),
                "action": st.sampled_from(["redact", "hash", "drop_event", "trigger_quarantine"]),
                "replacement_token": st.one_of(st.none(), st.text()),
            }
        )
    )
    return res


@st.composite
def draw_semantic_firewall_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "max_input_tokens": st.integers(min_value=1),
                "forbidden_intents": st.lists(st.text(), max_size=10),
                "action_on_violation": st.sampled_from(["drop", "quarantine", "redact"]),
            }
        )
    )
    return res


@st.composite
def draw_latent_smoothing_profile(draw: Any) -> dict[str, Any]:
    return {
        "decay_function": draw(st.sampled_from(["linear", "exponential", "cosine_annealing"])),
        "transition_window_tokens": draw(st.integers(min_value=1)),
        "decay_rate_param": draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False))),
    }


@st.composite
def draw_sae_latent_firewall(draw: Any) -> dict[str, Any]:
    action = draw(st.sampled_from(["clamp", "halt", "quarantine", "smooth_decay"]))
    clamp_val = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))
    smooth_prof = draw(st.one_of(st.none(), draw_latent_smoothing_profile()))

    # Satisfy the strict validation lock
    if action == "smooth_decay":
        if clamp_val is None:
            clamp_val = draw(st.floats(allow_nan=False, allow_infinity=False))
        if smooth_prof is None:
            smooth_prof = draw(draw_latent_smoothing_profile())

    return {
        "target_feature_index": draw(st.integers(min_value=0)),
        "monitored_layers": draw(st.lists(st.integers(min_value=0), min_size=1, max_size=10)),
        "max_activation_threshold": draw(st.floats(min_value=0.0, allow_nan=False, allow_infinity=False)),
        "violation_action": action,
        "clamp_value": clamp_val,
        "sae_dictionary_hash": draw(st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True)),
        "smoothing_profile": smooth_prof,
    }


@st.composite
def draw_information_flow_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "policy_id": st.text(),
                "active": st.booleans(),
                "rules": st.lists(draw_redaction_rule(), max_size=100),
                "semantic_firewall": st.one_of(st.none(), draw_semantic_firewall_policy()),
                "latent_firewalls": st.lists(draw_sae_latent_firewall(), max_size=10),
            }
        )
    )
    return res


information_flow_policy_adapter: TypeAdapter[InformationFlowPolicy] = TypeAdapter(InformationFlowPolicy)


@given(draw_information_flow_policy())
def test_dlp_policy_fuzzing(payload: dict[str, Any]) -> None:
    parsed = information_flow_policy_adapter.validate_python(payload)
    assert isinstance(parsed, InformationFlowPolicy)


@st.composite
def draw_state_patch(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "op": st.sampled_from(["add", "remove", "replace", "copy", "move", "test"]),
                "path": st.text(),
                "value": st.one_of(
                    st.none(), st.text(), st.integers(), st.booleans(), st.dictionaries(st.text(), st.text())
                ),
            }
        )
    )
    return res


@st.composite
def draw_state_diff(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "diff_id": st.text(),
                "author_node_id": st.text(
                    min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                ),
                "lamport_timestamp": st.integers(min_value=0),
                "vector_clock": st.dictionaries(
                    draw_did_string(),
                    st.integers(min_value=0),
                ),
                "patches": st.lists(draw_state_patch(), max_size=100),
            }
        )
    )
    return res


@st.composite
def draw_rollback_request(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "request_id": st.text(),
                "target_event_id": st.text(),
                "invalidated_node_ids": st.lists(st.text(), max_size=100),
            }
        )
    )
    return res


@st.composite
def draw_temporal_checkpoint(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "checkpoint_id": st.text(),
                "ledger_index": st.integers(min_value=0),
                "state_hash": st.text(),
            }
        )
    )
    return res


epistemic_ledger_adapter: TypeAdapter[EpistemicLedger] = TypeAdapter(EpistemicLedger)


@st.composite
def draw_any_state_event(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(_local_draw_any_state_event())
    return res


@st.composite
def draw_eviction_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "strategy": st.sampled_from(["fifo", "salience_decay", "summarize"]),
                "max_retained_tokens": st.integers(min_value=1),
                "protected_event_ids": st.lists(st.text(), max_size=100),
            }
        )
    )
    return res


@st.composite
def draw_migration_contract(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "contract_id": st.text(min_size=1),
                "source_version": st.text(min_size=1),
                "target_version": st.text(min_size=1),
                "path_transformations": st.dictionaries(st.text(min_size=1), st.text(min_size=1), max_size=10),
                "dropped_paths": st.lists(st.text(min_size=1), max_size=10),
            }
        )
    )
    return res


@st.composite
def draw_truth_maintenance_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "decay_propagation_rate": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "epistemic_quarantine_threshold": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "enforce_cross_agent_quarantine": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_defeasible_cascade(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "cascade_id": st.text(min_size=1),
                "root_falsified_event_id": st.text(),
                "propagated_decay_factor": st.floats(
                    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
                ),
                "quarantined_event_ids": st.lists(st.text(), min_size=1, max_size=100),
                "cross_boundary_quarantine_issued": st.booleans(),
            }
        )
    )
    return res


@st.composite
def draw_epistemic_ledger(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "history": st.lists(draw_any_state_event(), max_size=100),
                "checkpoints": st.lists(draw_temporal_checkpoint(), max_size=100),
                "active_rollbacks": st.lists(draw_rollback_request(), max_size=100),
                "eviction_policy": st.one_of(st.none(), draw_eviction_policy()),
                "migration_contracts": st.lists(draw_migration_contract(), max_size=10),
                "truth_maintenance_policy": st.one_of(st.none(), draw_truth_maintenance_policy()),
                "active_cascades": st.lists(draw_defeasible_cascade(), max_size=100),
            }
        )
    )
    return res


@settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
@given(draw_epistemic_ledger())
def test_differentials_routing(payload: dict[str, Any]) -> None:
    parsed = epistemic_ledger_adapter.validate_python(payload)
    assert isinstance(parsed, EpistemicLedger)


@st.composite
def draw_span_event(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "name": st.text(min_size=1),
                "timestamp_unix_nano": st.integers(min_value=0, max_value=2**63 - 1),
                "attributes": st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
            }
        )
    )
    return res


@st.composite
def draw_execution_span(draw: Any) -> dict[str, Any]:
    start_time_unix_nano = draw(st.integers(min_value=0, max_value=2**63 - 1))
    has_end_time = draw(st.booleans())
    end_time_unix_nano = None
    if has_end_time:
        delta = draw(st.integers(min_value=0, max_value=2**63 - 1))
        end_time_unix_nano = start_time_unix_nano + delta

    res: dict[str, Any] = {
        "trace_id": draw(st.text(min_size=1)),
        "span_id": draw(st.text(min_size=1)),
        "parent_span_id": draw(st.one_of(st.none(), st.text(min_size=1))),
        "name": draw(st.text(min_size=1)),
        "kind": draw(st.sampled_from(["client", "server", "producer", "consumer", "internal"])),
        "start_time_unix_nano": start_time_unix_nano,
        "end_time_unix_nano": end_time_unix_nano,
        "status": draw(st.sampled_from(["unset", "ok", "error"])),
        "events": draw(st.lists(draw_span_event(), max_size=100)),
    }
    return res


@st.composite
def draw_trace_export_batch(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "batch_id": st.text(min_size=1),
                "spans": st.lists(draw_execution_span(), max_size=100),
            }
        )
    )
    return res


trace_export_batch_adapter: TypeAdapter[TraceExportBatch] = TypeAdapter(TraceExportBatch)


@st.composite
def draw_custody_record(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "record_id": st.text(max_size=255),
                "source_node_id": st.text(max_size=255),
                "applied_policy_id": st.text(max_size=255),
                "pre_redaction_hash": st.one_of(st.none(), st.text(max_size=255)),
                "post_redaction_hash": st.text(max_size=255),
                "redaction_timestamp_unix_nano": st.integers(),
            }
        )
    )
    return res


custody_record_adapter: TypeAdapter[CustodyRecord] = TypeAdapter(CustodyRecord)


@given(draw_custody_record())
def test_custody_routing(payload: dict[str, Any]) -> None:
    parsed = custody_record_adapter.validate_python(payload)
    assert isinstance(parsed, CustodyRecord)


@given(draw_trace_export_batch())
def test_telemetry_routing(payload: dict[str, Any]) -> None:
    trace_export_batch_adapter.validate_python(payload)


@given(draw_interventional_causal_task())
def test_interventional_causal_task_routing(payload: dict[str, Any]) -> None:
    TypeAdapter(InterventionalCausalTask).validate_python(payload)


@given(draw_ontological_handshake())
def test_ontological_handshake_routing(payload: dict[str, Any]) -> None:
    TypeAdapter(OntologicalHandshake).validate_python(payload)


@st.composite
def draw_override_intent(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("override"),
                "authorized_node_id": draw_did_string(),
                "target_node_id": draw_did_string(),
                "override_action": st.dictionaries(
                    st.text(), st.one_of(st.text(), st.integers(), st.floats(), st.booleans(), st.none())
                ),
                "justification": st.text(max_size=2000),
            }
        )
    )
    return res


@st.composite
def draw_intervention_request(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("request"),
                "intervention_scope": st.none(),
                "fallback_sla": st.none(),
                "target_node_id": draw_did_string(),
                "context_summary": st.text(),
                "proposed_action": st.dictionaries(
                    st.text(), st.one_of(st.text(), st.integers(), st.floats(), st.booleans(), st.none())
                ),
                "adjudication_deadline": st.floats(allow_nan=False, allow_infinity=False),
            }
        )
    )
    return res


@st.composite
def draw_intervention_verdict(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("verdict"),
                "target_node_id": draw_did_string(),
                "approved": st.booleans(),
                "feedback": st.one_of(st.none(), st.text()),
            }
        )
    )
    return res


def draw_any_intervention_payload() -> st.SearchStrategy[dict[str, Any]]:
    return st.one_of(draw_intervention_request(), draw_intervention_verdict(), draw_override_intent())


intervention_payload_adapter: TypeAdapter[AnyInterventionPayload] = TypeAdapter(AnyInterventionPayload)


@given(draw_any_intervention_payload())
def test_anyinterventionpayload_routing(payload: dict[str, Any]) -> None:
    parsed = intervention_payload_adapter.validate_python(payload)
    payload_type = payload["type"]
    if payload_type == "request":
        assert isinstance(parsed, InterventionRequest)
    elif payload_type == "verdict":
        assert isinstance(parsed, InterventionVerdict)
    elif payload_type == "override":
        assert isinstance(parsed, OverrideIntent)


workflow_envelope_adapter: TypeAdapter[WorkflowEnvelope] = TypeAdapter(WorkflowEnvelope)


@st.composite
def draw_pq_signature(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "pq_algorithm": st.sampled_from(["ml-dsa", "slh-dsa", "falcon"]),
                "public_key_id": st.text(min_size=1),
                "pq_signature_blob": st.text(min_size=10, max_size=100000),
            }
        )
    )
    return res


@st.composite
def draw_bilateral_sla(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "receiving_tenant_id": st.text(min_size=1, max_size=255),
                "max_permitted_classification": st.sampled_from(
                    [
                        DataClassification.PUBLIC,
                        DataClassification.INTERNAL,
                        DataClassification.CONFIDENTIAL,
                        DataClassification.RESTRICTED,
                    ]
                ),
                "liability_limit_cents": st.integers(min_value=0),
                "permitted_geographic_regions": st.lists(st.text(min_size=1), max_size=10),
                "max_permitted_grid_carbon_intensity": st.one_of(
                    st.none(), st.floats(min_value=0.0, allow_nan=False, allow_infinity=False)
                ),
                "pq_signature": st.one_of(st.none(), draw_pq_signature()),
            }
        )
    )
    return res


@st.composite
def draw_workflow_envelope(draw: Any) -> dict[str, Any]:
    # We will generate a basic workflow envelope payload with optional tenant_id and session_id
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "manifest_version": st.sampled_from(["1.0.0", "1.1.0", "2.0.0"]),
                "topology": draw_evolutionary_topology_payload(),
                "governance": st.one_of(
                    st.none(),
                    st.fixed_dictionaries(
                        {
                            "max_budget_cents": st.integers(min_value=0),
                            "max_global_tokens": st.integers(),
                            "global_timeout_seconds": st.integers(min_value=0),
                            "formal_verification": st.one_of(st.none(), draw_formal_verification_contract()),
                        }
                    ),
                ),
                "tenant_id": st.one_of(st.none(), st.text(max_size=255)),
                "session_id": st.one_of(st.none(), st.text(max_size=255)),
                "max_risk_tolerance": st.one_of(
                    st.none(),
                    st.sampled_from([RiskLevel.SAFE, RiskLevel.STANDARD, RiskLevel.CRITICAL]),
                ),
                "allowed_data_classifications": st.one_of(
                    st.none(),
                    st.lists(
                        st.sampled_from(
                            [
                                DataClassification.PUBLIC,
                                DataClassification.INTERNAL,
                                DataClassification.CONFIDENTIAL,
                                DataClassification.RESTRICTED,
                            ]
                        ),
                        max_size=10,
                    ),
                ),
                "federated_sla": st.one_of(st.none(), draw_bilateral_sla()),
                "pq_signature": st.one_of(st.none(), draw_pq_signature()),
            }
        )
    )
    return res


@given(draw_workflow_envelope())
def test_workflow_envelope_fuzzing(payload: dict[str, Any]) -> None:
    parsed = workflow_envelope_adapter.validate_python(payload)
    assert isinstance(parsed, WorkflowEnvelope)


adversarial_adapter: TypeAdapter[AdversarialSimulationProfile] = TypeAdapter(AdversarialSimulationProfile)


@st.composite
def draw_adversarial_simulation_profile(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "simulation_id": st.text(min_size=1),
                "target_node_id": draw_did_string(),
                "attack_vector": st.sampled_from(
                    ["prompt_extraction", "data_exfiltration", "semantic_hijacking", "tool_poisoning"]
                ),
                "synthetic_payload": st.one_of(
                    st.text(), st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans()))
                ),
                "expected_firewall_trip": st.one_of(st.none(), st.text(min_size=1)),
            }
        )
    )
    return res


@given(draw_adversarial_simulation_profile())
def test_adversarial_simulation_routing(payload: dict[str, Any]) -> None:
    parsed = adversarial_adapter.validate_python(payload)
    assert isinstance(parsed, AdversarialSimulationProfile)
    assert parsed.simulation_id == payload["simulation_id"]
    assert parsed.target_node_id == payload["target_node_id"]


any_presentation_intent_adapter: TypeAdapter[AnyPresentationIntent] = TypeAdapter(AnyPresentationIntent)


@st.composite
def draw_informational_intent(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("informational"),
                "message": st.text(),
                "timeout_action": st.sampled_from(["rollback", "proceed_default", "terminate"]),
            }
        )
    )
    return res


@st.composite
def draw_drafting_intent(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("drafting"),
                "context_prompt": st.text(),
                "resolution_schema": st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
                "timeout_action": st.sampled_from(["rollback", "proceed_default", "terminate"]),
            }
        )
    )
    return res


@st.composite
def draw_adjudication_intent(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("forced_adjudication"),
                "deadlocked_claims": st.lists(st.text(), min_size=2),
                "resolution_schema": st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
                "timeout_action": st.sampled_from(["rollback", "proceed_default", "terminate"]),
            }
        )
    )
    return res


@st.composite
def draw_escalation_intent(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("escalation"),
                "tripped_rule_id": st.text(),
                "resolution_schema": st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
                "timeout_action": st.sampled_from(["rollback", "proceed_default", "terminate"]),
            }
        )
    )
    return res


@st.composite
def draw_any_presentation_intent(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.one_of(
            draw_informational_intent(),
            draw_drafting_intent(),
            draw_adjudication_intent(),
            draw_escalation_intent(),
        )
    )
    return res


@given(draw_any_presentation_intent())
def test_presentation_intent_routing(payload: dict[str, Any]) -> None:
    parsed = any_presentation_intent_adapter.validate_python(payload)
    if payload["type"] == "informational":
        assert isinstance(parsed, InformationalIntent)
        assert parsed.message == payload["message"]
    elif payload["type"] == "drafting":
        assert isinstance(parsed, DraftingIntent)
        assert parsed.context_prompt == payload["context_prompt"]
    elif payload["type"] == "forced_adjudication":
        assert isinstance(parsed, AdjudicationIntent)
        assert parsed.deadlocked_claims == payload["deadlocked_claims"]
    elif payload["type"] == "escalation":
        assert isinstance(parsed, EscalationIntent)
        assert parsed.tripped_rule_id == payload["tripped_rule_id"]


@st.composite
def draw_analogical_mapping_task(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "task_id": st.text(min_size=1),
                "source_domain": st.text(),
                "target_domain": st.text(),
                "required_isomorphisms": st.integers(min_value=1),
                "divergence_temperature_override": st.floats(min_value=0.0, allow_nan=False, allow_infinity=False),
            }
        )
    )
    return res


@st.composite
def draw_neuro_symbolic_handoff(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "handoff_id": st.text(min_size=1),
                "solver_protocol": st.sampled_from(["z3", "lean4", "coq", "tla_plus", "sympy"]),
                "formal_grammar_payload": st.text(),
                "expected_proof_schema": st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
                "timeout_ms": st.integers(min_value=1),
            }
        )
    )
    return res
