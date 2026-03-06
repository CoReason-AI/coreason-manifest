# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import re
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError

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
from coreason_manifest.presentation.scivis import AnyPanel, GrammarPanel, InsightCard
from coreason_manifest.state.argumentation import ArgumentGraph
from coreason_manifest.state.events import AnyStateEvent, BeliefUpdateEvent, ObservationEvent, SystemFaultEvent
from coreason_manifest.state.memory import EpistemicLedger
from coreason_manifest.state.semantic import SemanticEdge, SemanticNode
from coreason_manifest.telemetry.custody import CustodyRecord
from coreason_manifest.telemetry.schemas import TraceExportBatch
from coreason_manifest.testing.chaos import ChaosExperiment
from coreason_manifest.tooling import ActionSpace, ToolDefinition
from coreason_manifest.workflow.auctions import AuctionState
from coreason_manifest.workflow.envelope import WorkflowEnvelope
from coreason_manifest.workflow.nodes import AgentNode, AnyNode, CompositeNode, HumanNode, SystemNode
from coreason_manifest.workflow.topologies import AnyTopology, StateContract


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
def draw_agent_node_payload(draw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "agent", "description": draw(st.text())}
    if draw(st.booleans()):
        payload["intervention_policies"] = draw(st.lists(draw_intervention_policy(), max_size=100))
    if draw(st.booleans()):
        payload["action_space_id"] = draw(
            st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        )
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
def draw_consensus_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "strategy": st.sampled_from(["unanimous", "majority", "debate_rounds"]),
                "tie_breaker_node_id": st.one_of(
                    st.none(),
                    st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"),
                ),
                "max_debate_rounds": st.one_of(st.none(), st.integers(min_value=1, max_value=100)),
            }
        )
    )
    return res


def draw_topology_payload(nodes_strategy: st.SearchStrategy[dict[str, Any]]) -> st.SearchStrategy[dict[str, Any]]:
    dag_strategy = st.fixed_dictionaries(
        {
            "type": st.just("dag"),
            "nodes": st.dictionaries(
                st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"),
                nodes_strategy,
                max_size=5,
            ),
            "shared_state_contract": st.none(),
            "information_flow": st.none(),
            "observability": st.none(),
            "edges": st.just([]),
            "allow_cycles": st.booleans(),
            "backpressure": st.none(),
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
                st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"),
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
        }
    ).map(_council_mapper)

    return st.one_of(dag_strategy, council_strategy)


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
def draw_mutation_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "mutation_rate": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "temperature_shift_variance": st.floats(allow_nan=False, allow_infinity=False),
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
def _local_draw_any_state_event(draw: Any) -> dict[str, Any]:
    event_type = draw(st.sampled_from(["observation", "belief_update", "system_fault"]))
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
                st.text(
                    min_size=1,
                    max_size=128,
                    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
                ),
            )
        )
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


@given(st.text())
def test_anystateevent_invalid(invalid_type: str) -> None:
    if invalid_type in ["observation", "belief_update", "system_fault"]:
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
    st.text().filter(lambda x: not re.search(r"<\s*[a-zA-Z/]", x) and not re.search(r"on[a-zA-Z]+\s*=", x.lower())),
)
def test_anypanel_insight(title: str, content: str) -> None:
    payload = {"panel_id": "p3", "type": "insight_card", "title": title, "markdown_content": content}
    parsed = panel_adapter.validate_python(payload)
    assert isinstance(parsed, InsightCard)


@given(
    st.sampled_from(["quarantine", "circuit_breaker", "fallback"]),
    st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"),
    st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"),
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
                    ]
                ),
                "target_node_id": st.one_of(st.none(), st.text()),
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
                    }
                ),
                unique_by=lambda t: t["tool_name"] if isinstance(t, dict) and "tool_name" in t else str(t),
            ),
            "mcp_servers": st.lists(
                st.fixed_dictionaries(
                    {
                        "server_uri": st.text(),
                        "transport_type": st.sampled_from(["stdio", "sse", "http"]),
                        "allowed_mcp_tools": st.one_of(st.none(), st.lists(st.text(), max_size=100)),
                    }
                )
            ),
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
                    "extracted_by": st.text(
                        min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                    ),
                    "source_event_id": st.text(),
                    "spatial_anchor": st.one_of(st.none(), draw_spatial_anchor()),
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
                        "extracted_by": st.text(
                            min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                        ),
                        "source_event_id": st.text(),
                    }
                ),
            ),
            "temporal_bounds": st.one_of(st.none(), draw_temporal_bounds()),
        }
    )
)
def test_semanticedge_fuzzing(payload: dict[str, Any]) -> None:
    parsed = semantic_edge_adapter.validate_python(payload)
    assert isinstance(parsed, SemanticEdge)
    assert parsed.edge_id == payload["edge_id"]


@given(
    st.fixed_dictionaries(
        {
            "max_budget_cents": st.integers(min_value=0),
            "max_global_tokens": st.integers(),
            "global_timeout_seconds": st.integers(min_value=0),
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
                    st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"),
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
                "agent_id": st.text(),
                "estimated_cost_cents": st.integers(min_value=0),
                "estimated_latency_ms": st.integers(min_value=0),
                "confidence_score": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            }
        )
    )
    return res


@st.composite
def draw_task_award(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "task_id": st.text(),
                "awarded_agent_id": st.text(),
                "cleared_price_cents": st.integers(min_value=0),
            }
        )
    )
    return res


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
def draw_information_flow_policy(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "policy_id": st.text(),
                "active": st.booleans(),
                "rules": st.lists(draw_redaction_rule(), max_size=100),
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
def draw_epistemic_ledger(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "history": st.lists(draw_any_state_event(), max_size=100),
                "checkpoints": st.lists(draw_temporal_checkpoint(), max_size=100),
                "active_rollbacks": st.lists(draw_rollback_request(), max_size=100),
            }
        )
    )
    return res


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


@st.composite
def draw_override_intent(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "type": st.just("override"),
                "authorized_node_id": st.text(
                    min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                ),
                "target_node_id": st.text(
                    min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                ),
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
                "target_node_id": st.text(
                    min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                ),
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
                "target_node_id": st.text(
                    min_size=1, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                ),
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
                        }
                    ),
                ),
                "tenant_id": st.one_of(st.none(), st.text(max_size=255)),
                "session_id": st.one_of(st.none(), st.text(max_size=255)),
            }
        )
    )
    return res


@given(draw_workflow_envelope())
def test_workflow_envelope_fuzzing(payload: dict[str, Any]) -> None:
    parsed = workflow_envelope_adapter.validate_python(payload)
    assert isinstance(parsed, WorkflowEnvelope)
