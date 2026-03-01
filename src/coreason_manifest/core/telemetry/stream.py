from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.core.common.presentation import AdaptiveUIContract


class StreamError(BaseModel):
    """
    Strict error packet for stream multiplexing.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: int
    message: str
    severity: Literal["low", "medium", "high", "critical"]


class BaseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    trace_id: str | None = None
    timestamp: float


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
    p: list[dict[str, Any]]


# SOTA Python 3.12 Union syntax mapped to a Pydantic Discriminator
StreamPacket = Annotated[
    StreamErrorEnvelope
    | StreamDeltaEnvelope
    | StreamCloseEnvelope
    | StreamThoughtEnvelope
    | StreamToolCallEnvelope
    | StreamUIEnvelope
    | StreamStateDeltaEnvelope,
    Field(discriminator="op"),
]


class PacketContainer(BaseModel):
    """
    Container to facilitate validation and transport of StreamPackets.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    packet: StreamPacket
