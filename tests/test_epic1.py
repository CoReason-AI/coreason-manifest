import pytest
from pydantic import ValidationError

from coreason_manifest.causality import TraceContext
from coreason_manifest.state import StateVector
from coreason_manifest.envelope import ExecutionEnvelope
from coreason_manifest.spec.ontology import (
    ToolManifest,
    ActionSpaceManifest,
    PermissionBoundaryPolicy,
    SideEffectProfile,
)

def test_causal_integrity():
    A = TraceContext(
        trace_id="01HVK1Z5B7G6V5G8S8A2G1Z5B7",
        span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B8",
        parent_span_id=None,
        causal_clock=0
    )

    B = TraceContext(
        trace_id=A.trace_id,
        span_id="01HVK1Z5B7G6V5G8S8A2G1Z5B9",
        parent_span_id=A.span_id,
        causal_clock=A.causal_clock + 1
    )

    C = TraceContext(
        trace_id=A.trace_id,
        span_id="01HVK1Z5B7G6V5G8S8A2G1Z5BA",
        parent_span_id=B.span_id,
        causal_clock=B.causal_clock + 1
    )

    assert C.trace_id == A.trace_id
    assert C.causal_clock == A.causal_clock + 2

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
                            "trace_context": {},
                            "state_vector": {},
                            "payload": {
                                "type": "object",
                                "properties": {"system_prompt": {"type": "string"}}
                            }
                        },
                        "required": ["trace_context", "state_vector", "payload"]
                    },
                    side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
                    permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True)
                )
            ]
        )
    assert "attempts to define custom state management key 'system_prompt'" in str(excinfo.value)
