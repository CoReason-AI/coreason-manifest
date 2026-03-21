import pytest
from pydantic import ValidationError

from coreason_manifest.causality import TraceContext
from coreason_manifest.envelope import ExecutionEnvelope
from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    PermissionBoundaryPolicy,
    SideEffectProfile,
    ToolManifest,
)
from coreason_manifest.state import StateVector


def test_causal_integrity():
    a = TraceContext(
        trace_id="01HVK1Z5B7G6V5G8S8A2G1Z5B7",
        span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B8",
        parent_span_id=None,
        causal_clock=0
    )

    b = TraceContext(
        trace_id=a.trace_id,
        span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B9",
        parent_span_id=a.span_id,
        causal_clock=a.causal_clock + 1
    )

    c = TraceContext(
        trace_id=a.trace_id,
        span_id="01HVK1Z5B7G6V5G8S8A2G1Z5BA",
        parent_span_id=b.span_id,
        causal_clock=b.causal_clock + 1
    )

    assert c.trace_id == a.trace_id
    assert c.causal_clock == a.causal_clock + 2

    # Prevent superficial infinite self-pointers
    with pytest.raises(ValidationError):
        TraceContext(
            trace_id="01HVK1Z5B7G6V5G8S8A2G1Z5B7",
            span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B8",
            parent_span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B8",
            causal_clock=0
        )

def test_pure_function():
    # Attempt to pass an arbitrary configuration key (e.g., max_tokens or system_prompt) at the root level of the envelope
    with pytest.raises(ValidationError):
        ExecutionEnvelope(
            trace_context=TraceContext(trace_id="01HVK1Z5B7G6V5G8S8A2G1Z5B7", span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B8"),
            state_vector=StateVector(),
            payload={"test": "data"},
            system_prompt="This should fail"
        )

    with pytest.raises(ValidationError):
        ExecutionEnvelope(
            trace_context=TraceContext(trace_id="01HVK1Z5B7G6V5G8S8A2G1Z5B7", span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B8"),
            state_vector=StateVector(),
            payload={"test": "data"},
            max_tokens=500
        )

def test_delta_state():
    # Assert that a StateVector with is_delta=True passes validation even if mandatory mutable_memory keys are omitted (it can be None or empty)
    s = StateVector(is_delta=True)
    assert s.is_delta is True
    assert s.mutable_memory is None

def test_action_space_manifest_rejects_custom_state():
    with pytest.raises(ValidationError) as excinfo:
        ActionSpaceManifest(
            action_space_id="test_id",
            native_tools=[
                ToolManifest(
                    tool_name="test_tool",
                    description="test tool",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "system_prompt": {"type": "string"}
                        }
                    },
                    side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
                    permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True)
                )
            ]
        )
    assert "attempts to define reserved or illegal state management keys" in str(excinfo.value)

    # Should pass cleanly without any exceptions.
    ActionSpaceManifest(
        action_space_id="test_id_2",
        native_tools=[
            ToolManifest(
                tool_name="test_tool_2",
                description="test tool 2",
                input_schema={
                    "type": "object",
                    "properties": {
                        "sql_query": {"type": "string"}
                    }
                },
                side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
                permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True)
            )
        ]
    )
