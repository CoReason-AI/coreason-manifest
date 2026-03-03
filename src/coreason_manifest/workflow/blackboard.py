from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.state.ledger import EpistemicLedger


class TaskClaim(BaseModel):
    """
    Represents an exclusive claim on a task (event) by an agent.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    agent_signature: str = Field(..., description="The signature of the claiming agent.")
    expiry_timestamp: float = Field(..., description="The expiration timestamp of the lease.")


class BlackboardBrokerConfig(BaseModel):
    """
    A pure Pydantic schema representing the passive configuration/state
    definition of the blackboard broker.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, arbitrary_types_allowed=True)

    ledger: EpistemicLedger = Field(..., description="The EpistemicLedger attached to this broker.")
    # Map of event_type to a list of subscriber queue identifiers/URIs
    subscribers: dict[str, list[str]] = Field(default_factory=dict, description="Subscribers mapped by event type.")
    # Stores the current claims: event_id -> TaskClaim
    claims: dict[str, TaskClaim] = Field(default_factory=dict, description="Current task claims.")
