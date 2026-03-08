# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable scratchpad schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or downstream business logic. Focus purely on cryptographic
event sourcing, hardware attestations, and non-monotonic belief updates."""

from typing import Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class ThoughtBranch(CoreasonBaseModel):
    branch_id: str = Field(min_length=1, description="A deterministic capability pointer bounding this specific topological divergence in the Latent Scratchpad Trace.")
    parent_branch_id: str | None = Field(
        default=None, description="The branch this thought diverged from, enabling tree reconstruction."
    )
    latent_content_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 hash of the raw scratchpad text generated in this branch.",
    )
    prm_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="The logical validity score assigned to this branch by the Process Reward Model.",
    )


class LatentScratchpadTrace(CoreasonBaseModel):
    trace_id: str = Field(min_length=1, description="A Content Identifier (CID) bounding this ephemeral test-time execution tree.")
    explored_branches: list[ThoughtBranch] = Field(description="All logical paths the agent attempted within this Ephemeral Epistemic Quarantine—a volatile workspace where probability waves collapse before being committed to the immutable ledger.")
    discarded_branches: list[str] = Field(
        description="A list of Content Identifiers (CIDs) that were explicitly pruned due to logical dead-ends."
    )
    resolution_branch_id: str | None = Field(
        default=None,
        description="The Content Identifier (CID) that successfully resolved the uncertainty and led to the final output.",
    )
    total_latent_tokens: int = Field(ge=0, description="The total expenditure (in tokens) spent purely on internal reasoning.")

    @model_validator(mode="after")
    def verify_referential_integrity(self) -> Self:
        explored_branch_ids = {branch.branch_id for branch in self.explored_branches}

        if self.resolution_branch_id is not None and self.resolution_branch_id not in explored_branch_ids:
            raise ValueError(f"resolution_branch_id '{self.resolution_branch_id}' not found in explored_branches.")

        for discarded_id in self.discarded_branches:
            if discarded_id not in explored_branch_ids:
                raise ValueError(f"discarded branch '{discarded_id}' not found in explored_branches.")

        return self
