# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the dynamic routing and bypass schemas. This is a STRICTLY TOPOLOGICAL BOUNDARY.
These schemas act as a declarative Softmax Router Gate for the orchestrator. YOU ARE EXPLICITLY FORBIDDEN from
introducing kinetic network dispatch code or mutable state loops here. Focus purely on structural DAG definitions
and Merkle-DAG continuity receipts."""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.compute.inference import EpistemicCompressionSLA, EpistemicTransmutationTask
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID


class GlobalSemanticProfile(CoreasonBaseModel):
    """The immutable receipt of Step 1 ingestion acting as a static structural index of the artifact."""

    artifact_event_id: str = Field(
        min_length=1, description="The exact genesis CID of the document entering the routing tier."
    )
    detected_modalities: list[
        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]
    ] = Field(description="The strictly typed enum list of physical modalities detected in the artifact.")
    token_density: int = Field(
        ge=0, description="The mathematical token density used for downstream compute budget allocation."
    )


class BypassReceipt(CoreasonBaseModel):
    """The Merkle Null-Op preserving the topological chain of custody when an extraction node is intentionally
    skipped."""

    artifact_event_id: str = Field(
        min_length=1, description="The exact genesis CID of the document, ensuring continuity."
    )
    bypassed_node_id: NodeID = Field(
        description="The exact extraction step in the DAG that was mathematically starved of compute."
    )
    justification: Literal["modality_mismatch", "budget_exhaustion", "sla_timeout"] = Field(
        description="The deterministic reason the orchestrator severed this execution branch."
    )
    cryptographic_null_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 null-hash representing the skipped state to satisfy the Epistemic Ledger.",
    )


class DynamicRoutingManifest(CoreasonBaseModel):
    """The Softmax Router Gate dictating the active execution topology and spot compute allocation."""

    manifest_id: str = Field(min_length=1, description="The unique Content Identifier (CID) for this routing plan.")
    artifact_profile: GlobalSemanticProfile = Field(description="The semantic profile governing this route.")
    active_subgraphs: dict[str, list[NodeID]] = Field(
        description="Mapping of specific modalities (e.g., 'tabular_grid') to the explicit lists of worker NodeIDs "
        "authorized to execute."
    )
    bypassed_steps: list[BypassReceipt] = Field(
        default_factory=list, description="The declarative list of steps the orchestrator is mandated to skip."
    )
    branch_budgets_magnitude: dict[NodeID, int] = Field(
        description="The strict allocation of compute budget bound to specific nodes."
    )

    @model_validator(mode="after")
    def validate_modality_alignment(self) -> Self:
        """Mathematically proves that the router is not hallucinating graphs for non-existent modalities."""
        for modality in self.active_subgraphs:
            if modality not in self.artifact_profile.detected_modalities:
                raise ValueError(
                    f"Epistemic Violation: Cannot route to subgraph '{modality}' because it is missing from "
                    "detected_modalities."
                )
        return self

    @model_validator(mode="after")
    def validate_conservation_of_custody(self) -> Self:
        """Ensures bypass receipts do not contaminate cross-document boundaries."""
        for bypass in self.bypassed_steps:
            if bypass.artifact_event_id != self.artifact_profile.artifact_event_id:
                raise ValueError(
                    "Merkle Violation: BypassReceipt artifact_event_id does not match the root artifact_profile."
                )
        return self


def align_semantic_manifolds(
    task_id: str,
    source_modalities: list[str],
    target_modalities: list[Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]],
    artifact_event_id: str,
) -> EpistemicTransmutationTask | None:
    """
    A pure algebraic functor that calculates the epistemic gap between two nodes.
    If the target requires modalities absent in the source, it emits a deterministic Transmutation Task.
    """
    source_set = set(source_modalities)
    target_set = set(target_modalities)

    if target_set.issubset(source_set):
        return None

    require_dense = any(mod in ["raster_image", "tabular_grid"] for mod in target_modalities)
    density: Literal["sparse", "dense", "exhaustive"] = "dense" if require_dense else "sparse"

    sla = EpistemicCompressionSLA(
        strict_probability_retention=True, max_allowed_entropy_loss=0.01, required_grounding_density=density
    )

    return EpistemicTransmutationTask(
        task_id=task_id, artifact_event_id=artifact_event_id, target_modalities=target_modalities, compression_sla=sla
    )
