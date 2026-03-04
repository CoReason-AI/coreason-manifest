# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from coreason_manifest.core.primitives.wasm_types import WasiCapability, WasmResourceLimits
from coreason_manifest.workflow.nodes.base import Node


class WasmExecutionNode(Node):
    """
    A strictly declarative node defining a Zero-Trust Wasm/WASI Execution Sandboxing request.
    This does NOT execute Wasm. It only records the capabilities and limits requested.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    type: Literal["wasm_execution"] = Field(
        default="wasm_execution",
        description="Discriminator for Wasm execution nodes.",
    )

    wasm_module_hash: Annotated[
        str,
        Field(
            pattern=r"^[a-fA-F0-9]{64}$",
            description="The exact SHA-256 hash of the target Wasm module to execute.",
        ),
    ]

    resource_limits: WasmResourceLimits = Field(
        ...,
        description="Strict upper bounds on execution resources.",
    )

    capabilities: list[WasiCapability] = Field(
        default_factory=list,
        description="The strictly typed list of WASI capabilities requested by this node.",
    )
