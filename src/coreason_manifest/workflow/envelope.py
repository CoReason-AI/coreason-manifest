# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import DataClassification, RiskLevel, SemanticVersion
from coreason_manifest.oversight.governance import GlobalGovernance
from coreason_manifest.workflow.topologies import AnyTopology


class BilateralSLA(CoreasonBaseModel):
    receiving_tenant_id: str = Field(
        max_length=255, description="The strict enterprise identifier of the foreign B2B tenant receiving this payload."
    )
    max_permitted_classification: DataClassification = Field(
        description="The absolute highest data sensitivity allowed to cross this federated boundary."
    )
    liability_limit_cents: int = Field(ge=0, description="The strict financial cap on cross-tenant economic liability.")
    permitted_geographic_regions: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit whitelist of geographic regions or cloud enclaves where execution "
            "is legally permitted (Data Residency Pinning)."
        ),
    )


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
    max_risk_tolerance: RiskLevel | None = Field(
        default=None, description="The absolute maximum enterprise risk threshold permitted for this topology."
    )
    allowed_data_classifications: list[DataClassification] | None = Field(
        default=None,
        description="The declarative whitelist of data classifications permitted to flow through this graph.",
    )
    federated_sla: BilateralSLA | None = Field(
        default=None,
        description=(
            "The B2B Service Level Agreement contract that must be mathematically "
            "satisfied before multi-tenant graph coupling."
        ),
    )
