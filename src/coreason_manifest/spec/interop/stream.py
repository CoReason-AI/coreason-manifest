from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

class StreamError(BaseModel):
    """
    Strict error packet for stream multiplexing.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: int
    message: str
    severity: Literal["low", "medium", "high", "critical"]

# Union type for stream
StreamPacket = StreamError | dict[str, Any] | str

class PacketContainer(BaseModel):
    """
    Container to facilitate validation and transport of StreamPackets.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    packet: StreamPacket

    @model_validator(mode="before")
    @classmethod
    def duck_type_stream_packet(cls, data: Any) -> Any:
        """
        SOTA Ingress: Duck-type inference to upgrade raw dicts to rigid objects.
        """
        if isinstance(data, dict):
            # Access the 'packet' field.
            # Note: Input data to PacketContainer might be {'packet': ...}
            raw_pkt = data.get("packet")

            if isinstance(raw_pkt, dict):
                # Check signature
                required_keys = {"code", "message", "severity"}
                if required_keys <= raw_pkt.keys():
                    try:
                        # Attempt to cast to StreamError
                        # We construct it explicitly.
                        # Note: This might raise ValidationError if types are wrong (e.g. code is string "500" and strict=True)
                        # The prompt implies we should handle "generic JSON dictionaries".
                        # JSON numbers are ints/floats, so type should be fine.
                        # If we need coercion, we might need to handle it.
                        # But strict=True forbids coercion.
                        # The instruction says "matches the exact structural signature".

                        # Creating the object:
                        # We need to replace the dict in 'data' with the object.
                        # Since 'data' is a dict (input to PacketContainer), we modify it.

                        # We use model_validate to allow Pydantic to handle it?
                        # No, StreamError(**raw_pkt) works.

                        obj = StreamError.model_validate(raw_pkt) # enforce strictness
                        data["packet"] = obj
                    except Exception:
                        # If validation fails (e.g. types wrong), we leave it as dict
                        # and let the Union fallback to dict[str, Any]
                        pass
        return data
