# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
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
