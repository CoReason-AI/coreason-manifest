# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the declarative persistence schemas for Open Table Formats.
This is a STRICTLY STATIC BOUNDARY. These schemas represent the intent to write, not the execution of the write.
YOU ARE EXPLICITLY FORBIDDEN from introducing execution code, database driver imports, or active socket connections."""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class LakehouseMountConfig(CoreasonBaseModel):
    catalog_uri: str = Field(min_length=1, description="The stateless endpoint of the catalog (e.g., Polaris, Nessie).")
    table_format: Literal["iceberg", "delta", "hudi"] = Field(description="Strict boundary for the destination format.")
    schema_evolution_mode: Literal["strict", "additive_only"] = Field(
        description="Dictates if the agent can evolve the schema."
    )


class ContinuousMutationPolicy(CoreasonBaseModel):
    mutation_paradigm: Literal["append_only", "merge_on_read"] = Field(
        description="Forces non-destructive graph mutations."
    )
    max_uncommitted_rows: int = Field(gt=0, description="Backpressure threshold before forcing a commit.")
    micro_batch_interval_ms: int = Field(gt=0, description="Temporal bound for flushing the stream.")

    @model_validator(mode="after")
    def enforce_append_only_memory_bound(self) -> Self:
        """Mathematically prevent Out-Of-Memory (OOM) crashes by strictly bounding the buffer."""
        if self.mutation_paradigm == "append_only" and self.max_uncommitted_rows > 10000:
            raise ValueError("max_uncommitted_rows must be <= 10000 for append_only paradigm to prevent OOM crashes.")
        return self


class GraphFlatteningDirective(CoreasonBaseModel):
    node_projection_mode: Literal["wide_columnar", "struct_array"] = Field(description="How to flatten SemanticNode.")
    edge_projection_mode: Literal["adjacency_list", "map_array"] = Field(description="How to flatten SemanticEdge.")
    preserve_cryptographic_lineage: bool = Field(
        default=True,
        description="Forces the inclusion of MultimodalTokenAnchor hashes in the flattened row.",
    )
