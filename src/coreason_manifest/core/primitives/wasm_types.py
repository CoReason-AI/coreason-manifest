# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Literal

from pydantic import ConfigDict, Field

from coreason_manifest.core.common.base import CoreasonModel

# A discriminated union or literal-typed model representing specific sandbox permissions
type WasiCapability = Literal[
    "DirectoryReadCapability",
    "DirectoryWriteCapability",
    "NetworkFetchCapability",
    "SystemClockCapability",
    "RandomEntropyCapability",
]


class WasmResourceLimits(CoreasonModel):
    """
    Strict integers for `memory_limit_mb` and `instruction_fuel_limit`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    memory_limit_mb: int = Field(
        ...,
        gt=0,
        description="The maximum amount of memory (in megabytes) the Wasm module is allowed to allocate.",
    )
    instruction_fuel_limit: int = Field(
        ...,
        gt=0,
        description="The maximum number of instructions (fuel) the Wasm module is allowed to execute.",
    )
