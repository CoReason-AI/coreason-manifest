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


class StreamErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    op: Literal["error"]
    p: StreamError
    stream_id: str = Field(default="default")


class StreamDeltaEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    op: Literal["delta"]
    p: str
    stream_id: str = Field(default="default")


class StreamCloseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    op: Literal["close"]
    p: None = None
    stream_id: str = Field(default="default")


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
