# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.oversight.resilience import (
    AnyResiliencePayload,
    CircuitBreakerTrip,
    FallbackTrigger,
    QuarantineOrder,
)
from coreason_manifest.presentation.scivis import AnyPanel, CohortAttritionGrid, InsightCard, TimeSeriesPanel
from coreason_manifest.state.events import AnyStateEvent, BeliefUpdateEvent, ObservationEvent, SystemFaultEvent
from coreason_manifest.state.semantic import SemanticEdge, SemanticNode
from coreason_manifest.testing.chaos import ChaosExperiment
from coreason_manifest.workflow.nodes import AgentNode, AnyNode, HumanNode, SystemNode

node_adapter: TypeAdapter[AnyNode] = TypeAdapter(AnyNode)
chaos_adapter: TypeAdapter[ChaosExperiment] = TypeAdapter(ChaosExperiment)
event_adapter: TypeAdapter[AnyStateEvent] = TypeAdapter(AnyStateEvent)
panel_adapter: TypeAdapter[AnyPanel] = TypeAdapter(AnyPanel)
resilience_adapter: TypeAdapter[AnyResiliencePayload] = TypeAdapter(AnyResiliencePayload)
semantic_node_adapter: TypeAdapter[SemanticNode] = TypeAdapter(SemanticNode)
semantic_edge_adapter: TypeAdapter[SemanticEdge] = TypeAdapter(SemanticEdge)


@given(
    st.sampled_from(["agent", "human", "system"]),
    st.text(),
    st.one_of(
        st.none(),
        st.fixed_dictionaries(
            {
                "confidence_threshold": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "allowed_read_only_tools": st.lists(st.text()),
            }
        ),
    ),
    st.one_of(
        st.none(),
        st.fixed_dictionaries(
            {
                "active": st.booleans(),
                "dissonance_threshold": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                "action_on_gap": st.sampled_from(["fail", "probe", "clarify"]),
            }
        ),
    ),
    st.one_of(
        st.none(),
        st.fixed_dictionaries(
            {
                "max_loops": st.integers(min_value=0, max_value=50),
                "rollback_on_failure": st.booleans(),
            }
        ),
    ),
)
def test_anynode_routing(
    node_type: str,
    description: str,
    reflex_policy: dict[str, Any] | None,
    epistemic_policy: dict[str, Any] | None,
    correction_policy: dict[str, Any] | None,
) -> None:
    payload: dict[str, Any] = {"type": node_type, "description": description}
    if node_type == "agent":
        if reflex_policy is not None:
            payload["reflex_policy"] = reflex_policy
        if epistemic_policy is not None:
            payload["epistemic_policy"] = epistemic_policy
        if correction_policy is not None:
            payload["correction_policy"] = correction_policy

    parsed = node_adapter.validate_python(payload)
    if node_type == "agent":
        assert isinstance(parsed, AgentNode)
    elif node_type == "human":
        assert isinstance(parsed, HumanNode)
    elif node_type == "system":
        assert isinstance(parsed, SystemNode)


@given(st.text())
def test_anynode_invalid(invalid_type: str) -> None:
    if invalid_type in ["agent", "human", "system"]:
        return
    payload = {"type": invalid_type, "description": "test"}
    with pytest.raises(ValidationError):
        node_adapter.validate_python(payload)


@given(
    st.sampled_from(["observation", "belief_update", "system_fault"]),
    st.text(),
    st.floats(allow_nan=False, allow_infinity=False),
)
def test_anystateevent_routing(event_type: str, event_id: str, timestamp: float) -> None:
    payload = {"type": event_type, "event_id": event_id, "timestamp": timestamp}
    parsed = event_adapter.validate_python(payload)
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


@given(
    st.text(),
    st.text(),
    st.lists(
        st.dictionaries(
            st.text(), st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False))
        )
    ),
)
def test_anypanel_timeseries(x_axis: str, y_axis: str, data: list[dict[str, Any]]) -> None:
    payload = {
        "panel_id": "p1",
        "type": "timeseries",
        "x_axis_label": x_axis,
        "y_axis_label": y_axis,
        "data_series": data,
    }
    parsed = panel_adapter.validate_python(payload)
    assert isinstance(parsed, TimeSeriesPanel)


@given(
    st.lists(
        st.dictionaries(
            st.text(), st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False))
        )
    )
)
def test_anypanel_cohort(data: list[dict[str, Any]]) -> None:
    payload = {"panel_id": "p2", "type": "cohort_attrition", "grid_data": data}
    parsed = panel_adapter.validate_python(payload)
    assert isinstance(parsed, CohortAttritionGrid)


@given(
    st.text(), st.text().filter(lambda x: not any(tag in x.lower() for tag in ["<script", "<iframe", "javascript:"]))
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
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.one_of(st.none(), st.lists(st.text())),
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
            "node_id": st.text(),
            "label": st.text(),
            "text_chunk": st.text(),
            "embedding": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "vector": st.lists(st.floats(allow_nan=False, allow_infinity=False)),
                        "dimensionality": st.integers(),
                        "model_name": st.text(),
                    }
                ),
            ),
            "provenance": st.fixed_dictionaries(
                {
                    "extracted_by": st.text(
                        min_size=1, max_size=128, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                    ),
                    "source_event_id": st.text(),
                }
            ),
            "tier": st.sampled_from(["working", "episodic", "semantic"]),
            "temporal_bounds": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "valid_from": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                        "valid_to": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                        "interval_type": st.one_of(
                            st.none(),
                            st.sampled_from(["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]),
                        ),
                    }
                ),
            ),
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


@given(
    st.fixed_dictionaries(
        {
            "edge_id": st.text(),
            "subject_node_id": st.text(),
            "object_node_id": st.text(),
            "predicate": st.text(),
            "embedding": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "vector": st.lists(st.floats(allow_nan=False, allow_infinity=False)),
                        "dimensionality": st.integers(),
                        "model_name": st.text(),
                    }
                ),
            ),
            "provenance": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "extracted_by": st.text(
                            min_size=1, max_size=128, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                        ),
                        "source_event_id": st.text(),
                    }
                ),
            ),
            "temporal_bounds": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "valid_from": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                        "valid_to": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                        "interval_type": st.one_of(
                            st.none(),
                            st.sampled_from(["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]),
                        ),
                    }
                ),
            ),
        }
    )
)
def test_semanticedge_fuzzing(payload: dict[str, Any]) -> None:
    parsed = semantic_edge_adapter.validate_python(payload)
    assert isinstance(parsed, SemanticEdge)
