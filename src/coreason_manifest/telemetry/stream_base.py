from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class BaseEnvelope(CoreasonBaseModel):
    trace_id: str | None = Field(default=None, description="W3C Trace ID.")
    timestamp: float = Field(..., description="Unix timestamp.")
