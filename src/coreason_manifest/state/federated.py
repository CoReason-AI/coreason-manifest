from collections.abc import Mapping
from typing import Annotated

from pydantic import UUID4, Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.state.persistence import JSONPatchOperation


class VectorClock(CoreasonModel):
    """
    Represents a distributed logical clock to handle race conditions across
    different institutional servers without relying on absolute time.
    """

    ticks: Mapping[str, int] = Field(
        default_factory=dict,
        description="A dictionary mapping string institution_id to integer counters.",
    )


class FederatedStatePatch(CoreasonModel):
    """
    Represents a secure, CRDT-friendly payload to synchronize multi-agent state
    across institutional firewalls.
    """

    patch_id: Annotated[UUID4, Field(description="A UUID uniquely identifying the patch.")]
    originating_institution_id: Annotated[str, Field(description="The source institution ID that created this patch.")]
    target_workflow_id: Annotated[UUID4, Field(description="The UUID of the workflow to patch.")]
    vector_clock: Annotated[
        VectorClock, Field(description="The VectorClock timestamp representing the originating logic clock sequence.")
    ]
    operations: Annotated[
        tuple[JSONPatchOperation, ...],
        Field(description="The exact structural changes to the workflow state, representing JSON patch ops."),
    ]
    cryptographic_signature: Annotated[
        str, Field(description="A cryptographic hash string verifying the payload originated from its source securely.")
    ]


class FederatedSuspenseEnvelope(CoreasonModel):
    """
    A specialized interrupt contract for workflows that require multi-institutional sign-off.
    """

    envelope_id: Annotated[UUID4, Field(description="A UUID string uniquely identifying the envelope state event.")]
    required_signatures: Annotated[
        tuple[str, ...],
        Field(description="A list of institution_id strings that must approve the logic before the workflow resumes."),
    ]
    current_signatures: Annotated[
        tuple[str, ...], Field(description="A tracking list of collected approval signatures thus far.")
    ]
