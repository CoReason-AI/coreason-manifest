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
from coreason_manifest.workflow.nodes import AgentNode, AnyNode, HumanNode, SystemNode

node_adapter = TypeAdapter(AnyNode)
event_adapter = TypeAdapter(AnyStateEvent)
panel_adapter = TypeAdapter(AnyPanel)
resilience_adapter = TypeAdapter(AnyResiliencePayload)


@given(st.sampled_from(["agent", "human", "system"]), st.text())
def test_anynode_routing(node_type: str, description: str) -> None:
    payload = {"type": node_type, "description": description}
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
    payload = {"type": "timeseries", "x_axis_label": x_axis, "y_axis_label": y_axis, "data_series": data}
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
    payload = {"type": "cohort_attrition", "grid_data": data}
    parsed = panel_adapter.validate_python(payload)
    assert isinstance(parsed, CohortAttritionGrid)


@given(st.text(), st.text())
def test_anypanel_insight(title: str, content: str) -> None:
    payload = {"type": "insight_card", "title": title, "markdown_content": content}
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
