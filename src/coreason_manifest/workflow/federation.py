# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
from coreason_manifest.oversight.dlp import SecureSubSession
from coreason_manifest.workflow.envelope import BilateralSLA


class FederatedDiscoveryProtocol(CoreasonBaseModel):
    broadcast_endpoints: list[str] = Field(description="A list of MCP URI endpoints open for B2B task bidding.")
    supported_ontologies: list[str] = Field(
        description="A list of cryptographic hashes of domain ontologies this swarm is capable of processing."
    )


class CrossSwarmHandshake(CoreasonBaseModel):
    handshake_id: str = Field(description="Unique identifier for this B2B negotiation.")
    initiating_tenant_id: str = Field(description="The enterprise DID requesting the connection.")
    receiving_tenant_id: str = Field(description="The enterprise DID receiving the connection.")
    offered_sla: BilateralSLA = Field(description="The initial legal/data boundary proposed.")
    status: Literal["proposed", "negotiating", "aligned", "rejected"] = Field(
        default="proposed", description="The current status of the handshake."
    )


class FederatedCapabilityAttestation(CoreasonBaseModel):
    """
    An immutable cryptographic receipt proving an agent has the legal and structural authority
    to query a remote resource.
    """

    attestation_id: str = Field(min_length=1, description="Cryptographic Lineage Watermark for the attestation.")
    target_topology_id: NodeID = Field(description="The DID of the discovered external data lake/VPC.")
    authorized_session: SecureSubSession = Field(
        description="The isolated memory partition granted to the agent for this connection."
    )
    governing_sla: BilateralSLA = Field(
        description="The legal and physical boundary constraints for querying this target."
    )

    @model_validator(mode="after")
    def enforce_restricted_vault_locks(self) -> Self:
        if (
            self.governing_sla.max_permitted_classification == "restricted"
            and not self.authorized_session.allowed_vault_keys
        ):
            raise ValueError("RESTRICTED federated connections MUST define allowed_vault_keys in the SecureSubSession.")
        return self
