# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the orchestration constraint schemas. This is a STRICTLY TOPOLOGICAL BOUNDARY.
These schemas dictate the multi-agent graph geometry and decentralized routing mechanics. DO NOT inject procedural
execution code or synchronous blocking loops. Think purely in terms of graph theory, Byzantine fault tolerance, and
multi-agent market dynamics."""

from pydantic import BaseModel, Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class InputMapping(CoreasonBaseModel):
    """
    Dictates how keys from a parent's shared_state_contract map to a nested topology's state.
    """

    parent_key: str = Field(description="The key in the parent's shared state contract.")
    child_key: str = Field(description="The mapped key in the nested topology's state contract.")


class OutputMapping(CoreasonBaseModel):
    """
    Dictates how keys from a nested topology's state map back to a parent's shared_state_contract.
    """

    child_key: str = Field(description="The key in the nested topology's state contract.")
    parent_key: str = Field(description="The mapped key in the parent's shared state contract.")


class KinematicFeasibilityProof(BaseModel):
    """AGENT INSTRUCTION: This object represents an undeniable T-0 structural proof.
    Downstream orchestrators MUST verify these cryptographic receipts before igniting a graph.
    Do not bypass these checks.
    """

    substrate_availability_matrix: dict[str, str] = Field(
        ..., description="Map of NodeID to a SHA-256 VRAM/Compute lease receipt."
    )
    mcp_integration_hash: str = Field(
        ...,
        pattern=r"^[a-f0-9]{64}$",
        description="Merkle root of concatenated MCP tool schemas required by the graph.",
    )
    data_dimensionality_proof: str = Field(
        ..., pattern=r"^[a-f0-9]{64}$", description="Cryptographic signature of the tensor matrix bounds."
    )
    merkle_root_t0: str = Field(
        ..., pattern=r"^[a-f0-9]{64}$", description="Global state matrix hash at the instant of validation."
    )

    @model_validator(mode="after")
    def verify_substrate_leases_exist(self) -> "KinematicFeasibilityProof":
        if not self.substrate_availability_matrix:
            raise ValueError("A valid feasibility proof requires at least one substrate lease.")

        # Verify all receipts strictly conform to SHA-256 structure
        import re

        sha256_pattern = re.compile(r"^[a-f0-9]{64}$")
        for node_id, receipt in self.substrate_availability_matrix.items():
            if not sha256_pattern.match(receipt):
                raise ValueError(f"Invalid lease receipt for node {node_id}. Must be SHA-256.")

        return self
