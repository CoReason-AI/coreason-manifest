import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core import WasmExecutionReasoning, WasmMiddlewareDef


def test_wasm_execution_reasoning_success() -> None:
    model = WasmExecutionReasoning(
        model="wasm-model-1",
        memory_limit_mb=128,
        imported_host_functions=["console.log", "env.get_time"],
        wasi_capabilities=["network", "fs_read"],
    )

    assert model.type == "wasm_execution"  # noqa: S101
    assert model.memory_limit_mb == 128  # noqa: S101
    assert model.imported_host_functions == ["console.log", "env.get_time"]  # noqa: S101
    assert model.wasi_capabilities == ["network", "fs_read"]  # noqa: S101


def test_wasm_execution_reasoning_failure() -> None:
    # Missing required fields
    with pytest.raises(ValidationError):
        WasmExecutionReasoning(model="wasm-model-1", memory_limit_mb=128, imported_host_functions=["console.log"])  # type: ignore

    # Invalid type for memory_limit_mb
    with pytest.raises(ValidationError):
        WasmExecutionReasoning(
            model="wasm-model-1",
            memory_limit_mb="abc",  # type: ignore
            imported_host_functions=["console.log"],
            wasi_capabilities=["network"],
        )

    # Invalid wasi_capability
    with pytest.raises(ValidationError):
        WasmExecutionReasoning(
            model="wasm-model-1",
            memory_limit_mb=128,
            imported_host_functions=[],
            wasi_capabilities=["invalid_cap"],  # type: ignore
        )

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        WasmExecutionReasoning(
            model="wasm-model-1",
            memory_limit_mb=128,
            imported_host_functions=[],
            wasi_capabilities=["network"],
            extra_field="invalid",  # type: ignore
        )


def test_wasm_middleware_def_success() -> None:
    model = WasmMiddlewareDef()
    assert isinstance(model, WasmMiddlewareDef)  # noqa: S101


def test_wasm_middleware_def_failure() -> None:
    # Extra fields forbidden
    with pytest.raises(ValidationError):
        WasmMiddlewareDef(invalid_field="abc")  # type: ignore


def test_wasm_serialization() -> None:
    model = WasmExecutionReasoning(
        model="wasm-model-1",
        memory_limit_mb=512,
        imported_host_functions=["env.log"],
        wasi_capabilities=["clocks", "fs_write"],
    )

    json_str = model.model_dump_json(by_alias=True)
    assert "wasm_execution" in json_str  # noqa: S101
    assert "memory_limit_mb" in json_str  # noqa: S101
    assert "wasi_capabilities" in json_str  # noqa: S101
    assert "clocks" in json_str  # noqa: S101
