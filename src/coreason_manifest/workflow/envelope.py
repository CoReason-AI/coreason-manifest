# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import SemanticVersion
from coreason_manifest.oversight.governance import GlobalGovernance
from coreason_manifest.workflow.topologies import AnyTopology


class WorkflowEnvelope(CoreasonBaseModel):
    """
    The root envelope for an orchestrated workflow payload.
    """

    manifest_version: SemanticVersion = Field(description="The semantic version of this workflow manifestation schema.")
    topology: AnyTopology = Field(description="The underlying topology governing execution routing.")
    governance: GlobalGovernance | None = Field(
        default=None, description="Macro-economic circuit breakers and TTL limits for the swarm."
    )
    tenant_id: str | None = Field(
        default=None, max_length=255, description="The enterprise tenant boundary for this execution."
    )
    session_id: str | None = Field(
        default=None, max_length=255, description="The ephemeral session boundary for this execution."
    )
