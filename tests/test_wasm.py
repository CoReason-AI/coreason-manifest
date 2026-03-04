from datetime import UTC, datetime

from coreason_manifest.core.primitives.wasm_types import WasmResourceLimits
from coreason_manifest.state.events import EpistemicAnchor, EpistemicEvent, EventType, WasmExecutionTrace
from coreason_manifest.workflow.nodes.wasm import WasmExecutionNode


def test_wasm_resource_limits() -> None:
    limits = WasmResourceLimits(memory_limit_mb=128, instruction_fuel_limit=100000)
    assert limits.memory_limit_mb == 128
    assert limits.instruction_fuel_limit == 100000

def test_wasm_execution_node() -> None:
    node = WasmExecutionNode(
        id="wasm_node_1",
        type="wasm_execution",
        wasm_module_hash="a1b2c3d4e5f6e7f8a9b0c1d2e3f4a5b6c7d8e9f0",
        resource_limits=WasmResourceLimits(memory_limit_mb=128, instruction_fuel_limit=100000),
        capabilities=["DirectoryReadCapability"]
    )
    assert node.wasm_module_hash == "a1b2c3d4e5f6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"

def test_wasm_execution_trace() -> None:
    trace = WasmExecutionTrace(
        trace_type="wasm_execution",
        executed_module_hash="a1b2c3d4e5f6e7f8a9b0c1d2e3f4a5b6c7d8e9f0",
        granted_capabilities=["DirectoryReadCapability"],
        fuel_consumed=500,
        output_payload_hash="b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0a1"
    )
    event = EpistemicEvent(
        event_id="evt_123",
        timestamp=datetime.now(UTC),
        context_envelope={"hardware_cluster": "cluster-1", "agent_signature": "sig", "prompt_version": "v1"},
        event_type=EventType.STRUCTURAL_PARSED,
        payload=trace,
        epistemic_anchor=EpistemicAnchor(parent_event_id=None, spatial_coordinates=None)
    )
    assert event.payload.trace_type == "wasm_execution"
