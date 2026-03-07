# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class ThoughtBranch(CoreasonBaseModel):
    branch_id: str = Field(min_length=1, description="Unique identifier for this line of reasoning.")
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
    trace_id: str = Field(min_length=1, description="Unique identifier for this entire test-time compute session.")
    explored_branches: list[ThoughtBranch] = Field(description="All logical paths the agent attempted.")
    discarded_branches: list[str] = Field(
        description="A list of branch_ids that were explicitly pruned due to logical dead-ends."
    )
    resolution_branch_id: str | None = Field(
        default=None,
        description="The branch_id that successfully resolved the uncertainty and led to the final output.",
    )
    total_latent_tokens: int = Field(
        ge=0, description="The total compute expenditure (in tokens) spent purely on internal reasoning."
    )

    @model_validator(mode="after")
    def verify_referential_integrity(self) -> Self:
        explored_branch_ids = {branch.branch_id for branch in self.explored_branches}

        if self.resolution_branch_id is not None and self.resolution_branch_id not in explored_branch_ids:
            raise ValueError(f"resolution_branch_id '{self.resolution_branch_id}' not found in explored_branches.")

        for discarded_id in self.discarded_branches:
            if discarded_id not in explored_branch_ids:
                raise ValueError(f"discarded branch '{discarded_id}' not found in explored_branches.")

        return self
