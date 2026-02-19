from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict


class StreamError(BaseModel):
    """
    Strict error packet for stream multiplexing.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: int
    message: str
    severity: Literal["low", "medium", "high", "critical"]


def _duck_type_stream_error(v: Any) -> Any:
    """
    SOTA Ingress: Duck-type inference to upgrade raw dicts to rigid objects.
    """
    if isinstance(v, dict):
        # Check signature
        required_keys = {"code", "message", "severity"}
        if required_keys <= v.keys():
            try:
                # Attempt to cast to StreamError.
                # Use model_validate to allow Pydantic to handle strict validation.
                return StreamError.model_validate(v)
            except Exception:
                # If validation fails (e.g. types wrong), we return unmodified
                # and let the Union fallback to dict[str, Any]
                pass
    return v


# Union type for stream with intrinsic self-healing
StreamPacket = Annotated[
    StreamError | dict[str, Any] | str,
    BeforeValidator(_duck_type_stream_error),
]


class PacketContainer(BaseModel):
    """
    Container to facilitate validation and transport of StreamPackets.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    packet: StreamPacket
