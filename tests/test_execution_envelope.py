# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveActionSpaceManifest,
    ExecutionEnvelopeState,
    PermissionBoundaryPolicy,
    SideEffectProfile,
    SpatialToolManifest,
    StateVectorProfile,
    TraceContextState,
)


def test_causal_integrity() -> None:
    a = TraceContextState(
        trace_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B7",
        span_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B8",
        parent_span_cid=None,
        causal_clock=0,
    )

    b = TraceContextState(
        trace_cid=a.trace_cid,
        span_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B9",
        parent_span_cid=a.span_cid,
        causal_clock=a.causal_clock + 1,
    )

    c = TraceContextState(
        trace_cid=a.trace_cid,
        span_cid="01HVK1Z5B7G6V5G8S8A2G1Z5BA",
        parent_span_cid=b.span_cid,
        causal_clock=b.causal_clock + 1,
    )

    assert c.trace_cid == a.trace_cid
    assert c.causal_clock == a.causal_clock + 2

    # Prevent superficial infinite self-pointers
    with pytest.raises(ValidationError):
        TraceContextState(
            trace_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B7",
            span_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B8",
            parent_span_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B8",
            causal_clock=0,
        )


def test_pure_function() -> None:
    # Attempt to pass an arbitrary configuration key (e.g., max_tokens or system_prompt) at the root level of the envelope
    with pytest.raises(ValidationError):
        ExecutionEnvelopeState(
            trace_context=TraceContextState(
                trace_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B7", span_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B8"
            ),
            state_vector=StateVectorProfile(),
            payload={"test": "data"},
            system_prompt="This should fail",  # type: ignore[call-arg]
        )

    with pytest.raises(ValidationError):
        ExecutionEnvelopeState(
            trace_context=TraceContextState(
                trace_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B7", span_cid="01HVK1Z5B7G6V5G8S8A2G1Z5B8"
            ),
            state_vector=StateVectorProfile(),
            payload={"test": "data"},
            max_tokens=500,  # type: ignore[call-arg]
        )


def test_delta_state() -> None:
    # Assert that a StateVectorProfile with is_delta=True passes validation even if mandatory mutable_memory keys are omitted (it can be None or empty)
    s = StateVectorProfile(is_delta=True)
    assert s.is_delta is True
    assert s.mutable_memory is None


def test_action_space_manifest_rejects_custom_state() -> None:
    with pytest.raises(ValidationError) as excinfo:
        CognitiveActionSpaceManifest(
            action_space_cid="test_id",
            entry_point_cid="test_tool",
            transition_matrix={"test_tool": []},
            capabilities={
                "test_tool": SpatialToolManifest(
                    type="native_tool",
                    tool_name="test_tool",
                    description="test tool",
                    input_schema={"type": "object", "properties": {"system_prompt": {"type": "string"}}},
                    side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
                    permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
                )
            },
        )
    assert "Framework Violation" in str(excinfo.value)

    # Should pass cleanly without any exceptions.
    CognitiveActionSpaceManifest(
        action_space_cid="test_id_2",
        entry_point_cid="test_tool_2",
        transition_matrix={"test_tool_2": []},
        capabilities={
            "test_tool_2": SpatialToolManifest(
                type="native_tool",
                tool_name="test_tool_2",
                description="test tool 2",
                input_schema={"type": "object", "properties": {"sql_query": {"type": "string"}}},
                side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
                permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
            )
        },
    )


def test_state_vector_memory_bounds() -> None:
    import pytest
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import StateVectorProfile

    # It should pass with small valid dictionaries
    s = StateVectorProfile(mutable_memory={"test": "abc"}, read_only_context={"rules": "abc"})
    assert s.mutable_memory == {"test": "abc"}
    assert s.read_only_context == {"rules": "abc"}

    # It should fail with huge payloads exceeding nodes
    from typing import Any

    huge_dict: dict[str, Any] = {}
    for i in range(10001):
        huge_dict[f"key_{i}"] = i

    with pytest.raises(ValidationError) as exc_info:
        StateVectorProfile(mutable_memory=huge_dict)
    assert "Payload volume exceeds absolute hardware limit" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StateVectorProfile(read_only_context=huge_dict)
    assert "Payload volume exceeds absolute hardware limit" in str(exc_info.value)
