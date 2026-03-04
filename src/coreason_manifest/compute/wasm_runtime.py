"""
Wasm Execution Engine using wasmtime to replace legacy code execution.
"""
from typing import Any

import wasmtime
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class WasmExecutionEngine(BaseModel):
    """
    Zero-Trust WebAssembly execution engine.
    Ensures that agent-generated code runs in a sandboxed WASM environment
    with strict fuel (instruction count) and linear memory bounds.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_limit_mb: int = Field(default=128, description="Memory limit for the Wasm sandbox in megabytes.")
    fuel_limit: int = Field(default=10_000_000, description="Instruction count (fuel) limit.")

    _engine: wasmtime.Engine | None = PrivateAttr(default=None)
    _store: wasmtime.Store | None = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        """Initialize the wasmtime engine and store with limits."""
        config = wasmtime.Config()

        # Enforce execution bounds
        config.consume_fuel = True

        self._engine = wasmtime.Engine(config)
        self._store = wasmtime.Store(self._engine)

        # Inject instruction count budget
        self._store.set_fuel(self.fuel_limit)

        # Setup memory limits (memory limit handled during instantiation or linker config,
        # but configured in store for future allocation if needed)
        self._store.set_limits(
            memory_size=self.memory_limit_mb * 1024 * 1024
        )

    def execute_module(self, wasm_bytes: bytes, wasi_config: wasmtime.WasiConfig) -> None:
        """
        Compiles and executes a Wasm module given strict bytes and WASI capability config.
        """
        if self._engine is None or self._store is None:
            raise RuntimeError("WasmExecutionEngine not properly initialized.")

        module = wasmtime.Module(self._engine, wasm_bytes)

        linker = wasmtime.Linker(self._engine)
        linker.define_wasi()

        self._store.set_wasi(wasi_config)

        instance = linker.instantiate(self._store, module)
        exports = instance.exports(self._store)

        if "_start" in exports:
            start_func = exports["_start"]
            if isinstance(start_func, wasmtime.Func):
                start_func(self._store)
