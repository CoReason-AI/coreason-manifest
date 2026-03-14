# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Literal

from pydantic import Field, model_validator

from coreason_manifest.spec.ontology import CoreasonBaseState, NodeIdentifierState


class QueryLineageGraphRequest(CoreasonBaseState):
    """
    JSON-RPC payload schema complying with the Model Context Protocol (MCP) to allow
    external LLM agents to query the swarm's internal Merkle-DAGs without breaking zero-trust boundaries.
    """

    type: Literal["request"] = Field(
        default="request", description="The JSON-RPC discriminator."
    )
    target_merkle_root: str = Field(
        pattern="^[a-fA-F0-9]{64}$",
        description="The strictly typed SHA-256 Merkle root of the graph to query."
    )
    max_depth: int = Field(
        default=5, ge=1, le=50, description="The maximum traversal depth to prevent OOM/SSRF during graph projection."
    )


class QueryLineageGraphResponse(CoreasonBaseState):
    """
    JSON-RPC response payload schema complying with the Model Context Protocol (MCP).
    Returns a bounded structural projection of the requested lineage graph.
    """

    type: Literal["response"] = Field(
        default="response", description="The JSON-RPC discriminator."
    )
    queried_merkle_root: str = Field(
        pattern="^[a-fA-F0-9]{64}$",
        description="The strictly typed SHA-256 Merkle root that was queried."
    )
    discovered_nodes: list[NodeIdentifierState] = Field(
        description="The array of strictly bounded structural IDs discovered during the passive query traversal."
    )

    @model_validator(mode="after")
    def _sort_discovered_nodes(self) -> "QueryLineageGraphResponse":
        object.__setattr__(self, "discovered_nodes", sorted(self.discovered_nodes))
        return self


class SummarizeEpistemicReceiptRequest(CoreasonBaseState):
    """
    JSON-RPC payload schema complying with the Model Context Protocol (MCP) to allow
    external agents to request a summarization of a specific EpistemicProvenanceReceipt.
    """

    type: Literal["request"] = Field(
        default="request", description="The JSON-RPC discriminator."
    )
    receipt_cid: str = Field(
        min_length=1,
        description="The Content Identifier (CID) of the target EpistemicProvenanceReceipt."
    )
    summary_format: Literal["natural_language", "structured_json", "markdown_table"] = Field(
        default="structured_json",
        description="The requested deterministic format of the summary."
    )
