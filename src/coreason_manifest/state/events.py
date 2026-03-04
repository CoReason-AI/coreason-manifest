from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, Protocol, runtime_checkable

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.primitives.wasm_types import WasiCapability


@runtime_checkable
class ContextEnvelopeProtocol(Protocol):
    """
    Mock protocol for external telemetry envelopes representing hardware,
    prompt version, agent signature, etc.
    """

    hardware_cluster: str
    agent_signature: str
    prompt_version: str


class EventType(StrEnum):
    """
    The type of epistemic event occurring in the system.
    """

    STRUCTURAL_PARSED = "STRUCTURAL_PARSED"
    SEMANTIC_EXTRACTED = "SEMANTIC_EXTRACTED"
    WASM_EXECUTION_TRACE_RECORDED = "WASM_EXECUTION_TRACE_RECORDED"
    # Other event types can be added here


class WasmExecutionTrace(CoreasonModel):
    """
    Records the exact deterministic outcome of the external execution of a Wasm module.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    trace_type: Literal["wasm_execution"] = Field("wasm_execution", description="Tagged union discriminator.")
    executed_module_hash: str = Field(
        ...,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="The exact SHA-256 hash of the target Wasm module executed.",
    )
    granted_capabilities: list[WasiCapability] = Field(
        ...,
        description="The strictly typed list of WASI capabilities the runner actually allowed.",
    )
    fuel_consumed: int = Field(
        ...,
        ge=0,
        description="The number of instructions (fuel) consumed during execution.",
    )
    output_payload_hash: str = Field(
        ...,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="The exact SHA-256 hash of the output payload generated.",
    )


class LegacyPayload(CoreasonModel):
    """
    Fallback payload for legacy un-discriminated events.
    """

    model_config = ConfigDict(extra="allow", frozen=True)
    trace_type: Literal["legacy_payload"] = Field("legacy_payload", description="Tagged union discriminator.")


class EpistemicAnchor(CoreasonModel):
    """
    A reference to maintain the Chain of Custody.
    """

    parent_event_id: str | None = Field(
        default=None, description="The ID of the parent event that caused this event, if any."
    )
    spatial_coordinates: list[float] | None = Field(
        default=None, description="Bounding box coordinates (e.g., [x1, y1, x2, y2]) to anchor to a specific region."
    )


class EpistemicEvent(CoreasonModel):
    """
    An immutable event appended to the ledger representing a state mutation.
    """

    event_id: str = Field(..., description="A unique UUID/ULID for the event.")
    timestamp: datetime = Field(..., description="UTC datetime when the event occurred.")
    context_envelope: dict[str, Any] = Field(
        ..., description="A generic dict or Protocol representing hardware, prompt version, agent signature."
    )
    event_type: EventType = Field(..., description="The type of the event.")
    payload: Annotated[
        WasmExecutionTrace | LegacyPayload, Field(discriminator="trace_type", description="The actual data mutation.")
    ]
    epistemic_anchor: EpistemicAnchor = Field(
        ..., description="A reference to the parent event and spatial coordinates."
    )

    @model_validator(mode="after")
    def validate_utc(self) -> "EpistemicEvent":
        """Ensure the timestamp is UTC."""
        if self.timestamp.tzinfo is None or self.timestamp.tzinfo != UTC:
            # We enforce UTC strictly for the distributed ledger
            raise ValueError("Timestamp must be timezone-aware and set to UTC.")
        return self
