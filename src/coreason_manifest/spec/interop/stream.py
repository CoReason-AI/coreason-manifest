from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class StreamError(BaseModel):
    """
    Strict error packet for stream multiplexing.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: int
    message: str
    severity: Literal["low", "medium", "high", "critical"]


class BaseStreamEnvelope(BaseModel):
    """
    Base class for all stream envelopes, enforcing strict configuration and stream ID.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    stream_id: str = Field(default="default", min_length=1, pattern=r"^[a-zA-Z0-9_\-\.:]+$")


class StreamErrorEnvelope(BaseStreamEnvelope):
    op: Literal["error"]
    p: StreamError


class StreamDeltaEnvelope(BaseStreamEnvelope):
    op: Literal["delta"]
    p: str


class StreamCloseEnvelope(BaseStreamEnvelope):
    op: Literal["close"]
    p: None = None


# SOTA Python 3.12 Union syntax mapped to a Pydantic Discriminator
StreamPacket = Annotated[
    StreamErrorEnvelope | StreamDeltaEnvelope | StreamCloseEnvelope,
    Field(discriminator="op"),
]


class PacketContainer(BaseModel):
    """
    Container to facilitate validation and transport of StreamPackets.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    packet: StreamPacket
