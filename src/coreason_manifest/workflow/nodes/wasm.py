from typing import Literal

from pydantic import ConfigDict, Field

from coreason_manifest.core.primitives.types import GitSHA
from coreason_manifest.core.primitives.wasm_types import WasiCapability, WasmResourceLimits
from coreason_manifest.workflow.nodes.base import Node


class WasmExecutionNode(Node):
    model_config = ConfigDict(extra="forbid")

    type: Literal["wasm_execution"] = Field(
        "wasm_execution", description="Node type for zero-trust Wasm/WASI execution."
    )
    wasm_module_hash: GitSHA = Field(..., description="SHA-256 hash or Git SHA identifying the WebAssembly module.")
    resource_limits: WasmResourceLimits = Field(..., description="Strict execution constraints for fuel and memory.")
    capabilities: list[WasiCapability] = Field(
        default_factory=list, description="Strictly typed list of WASI capabilities requested."
    )
