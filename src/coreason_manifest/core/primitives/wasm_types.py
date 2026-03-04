from typing import Literal

from pydantic import ConfigDict, Field

from coreason_manifest.core.common.base import CoreasonModel

type WasiCapability = Literal[
    "DirectoryReadCapability",
    "DirectoryWriteCapability",
    "NetworkFetchCapability",
    "ClockCapability",
    "RandomCapability",
]


class WasmResourceLimits(CoreasonModel):
    model_config = ConfigDict(extra="forbid")

    memory_limit_mb: int = Field(..., strict=True, description="Strict memory limit in MB for the Wasm execution.")
    instruction_fuel_limit: int = Field(..., strict=True, description="Maximum amount of instruction fuel allowed.")
