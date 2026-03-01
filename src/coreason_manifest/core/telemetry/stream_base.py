from pydantic import BaseModel, ConfigDict

class BaseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    trace_id: str | None = None
    timestamp: float
