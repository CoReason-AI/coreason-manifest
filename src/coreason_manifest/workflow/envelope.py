from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import SemanticVersion  # noqa: TC001
from coreason_manifest.workflow.topologies import AnyTopology  # noqa: TC001


class WorkflowEnvelope(CoreasonBaseModel):
    """
    The root envelope for an orchestrated workflow payload.
    """

    manifest_version: SemanticVersion = Field(description="The semantic version of this workflow manifestation schema.")
    topology: AnyTopology = Field(description="The underlying topology governing execution routing.")
