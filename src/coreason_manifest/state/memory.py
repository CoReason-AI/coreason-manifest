from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.state.events import AnyStateEvent  # noqa: TC001


class EpistemicLedger(CoreasonBaseModel):
    history: list[AnyStateEvent] = Field(description="An append-only, cryptographic ledger of state events.")


class WorkingMemorySnapshot(CoreasonBaseModel):
    system_prompt: str = Field(description="The active system prompt guiding the agent's behavior.")
    active_context: dict[str, str] = Field(
        description="A dictionary representing the active context variables for the agent."
    )


class FederatedStateSnapshot(CoreasonBaseModel):
    topology_id: str | None = Field(
        default=None, description="The identifier of the federated topology, if applicable."
    )
