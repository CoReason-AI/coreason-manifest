from pydantic import ConfigDict

from coreason_manifest.core.common.base import CoreasonModel


class BaseEnvelope(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    trace_id: str | None = None
    timestamp: float
