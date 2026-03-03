from typing import Annotated, Any, Literal

from pydantic import ConfigDict, Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.presentation import AdaptiveUIContract
from coreason_manifest.state.persistence import JSONPatchOperation
from coreason_manifest.telemetry.custody import EpistemicEnvelope
from coreason_manifest.telemetry.stream_base import BaseEnvelope
from coreason_manifest.telemetry.suspense_envelope import StreamSuspenseEnvelope


class StreamError(CoreasonModel):
    """
    Strict error packet for stream multiplexing.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: int
    message: str
    severity: Literal["low", "medium", "high", "critical"]


class StreamErrorEnvelope(BaseEnvelope):
    op: Literal["error"]
    p: StreamError


class StreamDeltaEnvelope(BaseEnvelope):
    op: Literal["delta"]
    p: str


class StreamCloseEnvelope(BaseEnvelope):
    op: Literal["close"]
    p: None = None


class StreamThoughtEnvelope(BaseEnvelope):
    op: Literal["thought"]
    p: str


class StreamToolCallEnvelope(BaseEnvelope):
    op: Literal["tool_call"]
    p: dict[str, Any]


class StreamUIEnvelope(BaseEnvelope):
    op: Literal["ui_mount"]
    p: AdaptiveUIContract


class StreamStateDeltaEnvelope(BaseEnvelope):
    op: Literal["state_delta"]
    p: list[JSONPatchOperation]


class StreamEpistemicEnvelope(BaseEnvelope):
    op: Literal["epistemic"]
    p: EpistemicEnvelope


# PEP 695 Type Aliasing mapped to a Pydantic Discriminator
StreamPacket = Annotated[
    StreamErrorEnvelope
    | StreamDeltaEnvelope
    | StreamCloseEnvelope
    | StreamThoughtEnvelope
    | StreamToolCallEnvelope
    | StreamUIEnvelope
    | StreamStateDeltaEnvelope
    | StreamSuspenseEnvelope
    | StreamEpistemicEnvelope,
    Field(discriminator="op"),
]


class PacketContainer(CoreasonModel):
    """
    Container to facilitate validation and transport of StreamPackets.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    packet: StreamPacket
