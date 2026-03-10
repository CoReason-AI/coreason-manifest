# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import hashlib
from typing import Literal

from pydantic import ValidationError

from ..spec.ontology import (
    AnyTopologyManifest,
    EpistemicCompressionSLA,
    EpistemicTransmutationTask,
    ExecutionNodeReceipt,
    System2RemediationIntent,
)


def generate_correction_prompt(error: ValidationError, target_node_id: str, fault_id: str) -> System2RemediationIntent:
    """
    Pure functional adapter. Maps a raw Pythonic pydantic.ValidationError into a
    language-model-legible System2RemediationIntent without triggering runtime side effects.
    """
    failing_pointers: list[str] = []
    error_messages: list[str] = []
    for err in error.errors():
        loc_path = "".join(f"/{item!s}" for item in err["loc"]) if err["loc"] else "/"
        failing_pointers.append(loc_path)
        err_type = err.get("type", "unknown")
        if err_type == "missing":
            error_messages.append(
                f"The required semantic boundary at '{loc_path}' is completely missing. You must project this missing dimension to satisfy the StateContract."  # noqa: E501
            )
        else:
            msg = err.get("msg", "Invalid structural payload.")
            error_messages.append(f"A structural boundary violation occurred at '{loc_path}': {msg}")
    failing_pointers = list(set(failing_pointers))
    remediation_prompt = (
        "CRITICAL CONTRACT BREACH: Your generated state representation violates the formal ontological boundaries of the Shared Kernel. Review the following strict topological failures and correct your JSON projection:\n"  # noqa: E501
        + "\n".join(f"- {msg}" for msg in error_messages)
    )
    return System2RemediationIntent(
        fault_id=fault_id,
        target_node_id=target_node_id,
        failing_pointers=failing_pointers,
        remediation_prompt=remediation_prompt,
    )


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


def compute_topology_hash(topology: "AnyTopologyManifest") -> str:
    """
    Deterministically computes the SOTA Merkle-DAG SHA-256 fingerprint of a given topology.
    """
    return hashlib.sha256(topology.model_dump_canonical()).hexdigest()


def verify_merkle_proof(trace: list[ExecutionNodeReceipt]) -> bool:
    """
    Verifies a Merkle DAG trace of execution nodes.
    Ensures that every node's hash is computationally valid and mathematically
    sound (matching canonical inputs/outputs) and topologically links correctly
    via Kahn's concept of parent hashes regardless of the temporal array index order.

    Returns True if validation succeeds, False otherwise.
    """
    node_map: dict[str, ExecutionNodeReceipt] = {}
    for node in trace:
        if node.node_hash is None:
            return False
        node_map[node.node_hash] = node
    for node in trace:
        if node.generate_node_hash() != node.node_hash:
            return False
        for parent_hash in node.parent_hashes:
            if parent_hash not in node_map:
                return False
    return True
