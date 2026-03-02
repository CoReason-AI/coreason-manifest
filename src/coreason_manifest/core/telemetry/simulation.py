# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum
from typing import Any

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel


class PatchOp(StrEnum):
    """RFC 6902 JSON Patch operations."""

    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    MOVE = "move"
    COPY = "copy"
    TEST = "test"


class JSONPatchOperation(CoreasonModel, frozen=True, extra="forbid"):
    """
    RFC 6902 standard patch operation.
    """

    op: PatchOp = Field(..., description="The operation to perform.")
    path: str = Field(..., description="A JSON Pointer path.")
    value: Any | None = Field(default=None, description="The value to add, replace or test.")
    from_: str | None = Field(
        default=None, alias="from", description="A JSON Pointer path pointing to the location to move/copy from."
    )


class SimulationStep(CoreasonModel, frozen=True, extra="forbid"):
    """
    Offline evaluation envelope mirroring live telemetry.
    """

    traceparent: str = Field(..., description="W3C traceparent string.")
    tracestate: str = Field(..., description="W3C tracestate string.")
    state_mutations: list[JSONPatchOperation] = Field(default_factory=list, description="RFC 6902 state mutations.")
    execution_hash: str = Field(..., description="Cryptographic lineage hash to prevent eval-washing.")
    thought: str | dict[str, Any] | None = Field(default=None, description="Multimodal thought payload.")


class SimulationTrace(CoreasonModel, frozen=True, extra="forbid"):
    """
    Replayable journal architecture containing simulation steps.
    """

    steps: list[SimulationStep] = Field(default_factory=list, description="List of offline evaluation steps.")
