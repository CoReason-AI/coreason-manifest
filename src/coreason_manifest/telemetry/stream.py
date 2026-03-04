from typing import Any, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.common.presentation import AdaptiveUIContract
from coreason_manifest.state.persistence import JSONPatchOperation
from coreason_manifest.telemetry.custody import EpistemicEnvelope
from coreason_manifest.telemetry.stream_base import BaseEnvelope
from coreason_manifest.telemetry.suspense_envelope import StreamSuspenseEnvelope


class StreamError(CoreasonBaseModel):
    """
    Strict error packet for stream multiplexing.
    """

    code: int = Field(..., description="The HTTP or internal error code.")
    message: str = Field(..., description="Human-readable error message.")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="The severity level of the error.")


class StreamErrorEnvelope(BaseEnvelope):
    op: Literal["error"] = Field("error", description="Discriminator field.")
    p: StreamError = Field(..., description="The error packet payload.")


class StreamDeltaEnvelope(BaseEnvelope):
    op: Literal["delta"] = Field("delta", description="Discriminator field.")
    p: str = Field(..., description="The delta string.")


class StreamCloseEnvelope(BaseEnvelope):
    op: Literal["close"] = Field("close", description="Discriminator field.")
    p: None = Field(default=None, description="Empty payload for stream closure.")


class StreamThoughtEnvelope(BaseEnvelope):
    op: Literal["thought"] = Field("thought", description="Discriminator field.")
    p: str = Field(..., description="The thought content.")


class StreamToolCallEnvelope(BaseEnvelope):
    op: Literal["tool_call"] = Field("tool_call", description="Discriminator field.")
    p: dict[str, Any] = Field(..., description="The tool call content.")


class StreamUIEnvelope(BaseEnvelope):
    op: Literal["ui_mount"] = Field("ui_mount", description="Discriminator field.")
    p: AdaptiveUIContract = Field(..., description="The UI mount configuration.")


class StreamStateDeltaEnvelope(BaseEnvelope):
    op: Literal["state_delta"] = Field("state_delta", description="Discriminator field.")
    p: list[JSONPatchOperation] = Field(..., description="The state delta JSON patch operations.")


class StreamEpistemicEnvelope(BaseEnvelope):
    op: Literal["epistemic"] = Field("epistemic", description="Discriminator field.")
    p: EpistemicEnvelope = Field(..., description="The epistemic envelope content.")


# PEP 695 Type Aliasing mapped to a Pydantic Discriminator
type StreamPacket = (
    StreamErrorEnvelope
    | StreamDeltaEnvelope
    | StreamCloseEnvelope
    | StreamThoughtEnvelope
    | StreamToolCallEnvelope
    | StreamUIEnvelope
    | StreamStateDeltaEnvelope
    | StreamSuspenseEnvelope
    | StreamEpistemicEnvelope
)


class PacketContainer(CoreasonBaseModel):
    """
    Container to facilitate validation and transport of StreamPackets.
    """

    packet: StreamPacket = Field(..., discriminator="op")
