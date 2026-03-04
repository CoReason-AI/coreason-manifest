from coreason_manifest.core.primitives.wasm_types import WasmResourceLimits
from coreason_manifest.state.events import WasmExecutionTrace
from coreason_manifest.workflow.nodes.wasm import WasmExecutionNode


def test_wasm_execution_node() -> None:
    node = WasmExecutionNode(
        id="wasm_node",
        wasm_module_hash="a" * 64,
        resource_limits=WasmResourceLimits(memory_limit_mb=128, instruction_fuel_limit=1000000),
        capabilities=["DirectoryReadCapability", "NetworkFetchCapability"],
    )
    assert node.type == "wasm_execution"
    assert node.wasm_module_hash == "a" * 64
    assert node.resource_limits.memory_limit_mb == 128
    assert node.resource_limits.instruction_fuel_limit == 1000000
    assert len(node.capabilities) == 2


def test_wasm_execution_trace() -> None:
    trace = WasmExecutionTrace(
        trace_type="wasm_execution",
        executed_module_hash="a" * 64,
        granted_capabilities=["DirectoryReadCapability"],
        fuel_consumed=50000,
        output_payload_hash="b" * 64,
    )
    assert trace.trace_type == "wasm_execution"
    assert trace.executed_module_hash == "a" * 64
    assert trace.fuel_consumed == 50000
    assert trace.output_payload_hash == "b" * 64
    assert len(trace.granted_capabilities) == 1
