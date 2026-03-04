from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class AmbientSignal(CoreasonBaseModel):
    """
    Lightweight UX signal for UI rendering of progress.
    """

    status_message: str = Field(description="A human-readable status message for the current task.")
    progress: float | None = Field(
        default=None, description="The progress ratio from 0.0 to 1.0, or None if indeterminate."
    )


class SuspenseEnvelope(CoreasonBaseModel):
    """
    Indicates that the swarm is waiting on a long-running process or human input.
    """
