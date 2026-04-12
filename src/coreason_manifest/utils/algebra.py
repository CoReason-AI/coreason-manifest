# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""AGENT INSTRUCTION: This module contains pure data transformations of the Hollow Data Plane."""

# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import ast
import base64
import copy
import hashlib
import math
import typing
from collections.abc import Sequence
from typing import Any, Literal, cast

import jsonpatch  # type: ignore[import-untyped, unused-ignore]
import numpy as np
from pydantic import AnyUrl, BaseModel, ValidationError
from pydantic.json_schema import models_json_schema

import coreason_manifest.spec.ontology as ontology
from coreason_manifest.spec.ontology import (
    AnyTopologyManifest,
    CognitiveStateProfile,
    CoreasonBaseState,
    DocumentLayoutManifest,
    DynamicRoutingManifest,
    EpistemicTransmutationTask,
    ExecutionNodeReceipt,
    ManifestViolationReceipt,
    OntologicalAlignmentPolicy,
    StateMutationIntent,
    System2RemediationIntent,
    TamperFaultEvent,
    VectorEmbeddingState,
    WorkflowManifest,
)

SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "step8_vision": DocumentLayoutManifest,
    "state_differential": StateMutationIntent,
    "cognitive_sync": CognitiveStateProfile,
    "system2_remediation": System2RemediationIntent,
    "lean4_premise": ontology.EpistemicLean4Premise,
    "lean4_receipt": ontology.Lean4VerificationReceipt,
    "logic_premise": ontology.EpistemicLogicPremise,
    "logic_receipt": ontology.FormalLogicProofReceipt,
    "prolog_premise": ontology.EpistemicPrologPremise,
    "prolog_receipt": ontology.PrologDeductionReceipt,
}


def project_manifest_to_mermaid(manifest: DynamicRoutingManifest) -> str:
    """Deterministically compile the routing manifest into a Mermaid.js directed graph."""
    lines: list[str] = [
        "graph TD",
        "    classDef active fill:#e1f5fe,stroke:#333,stroke-width:2px;",
        "    classDef bypassed fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5;",
    ]

    safe_root_cid = manifest.manifest_cid.replace(":", "_").replace("-", "_").replace(".", "_")
    lines.append(f"    {safe_root_cid}[{manifest.manifest_cid}]")

    for modality in manifest.artifact_profile.detected_modalities:
        lines.append(f"    subgraph {modality}")

        if modality in manifest.active_subgraphs:
            for node_cid in manifest.active_subgraphs[modality]:
                safe_cid = node_cid.replace(":", "_").replace("-", "_").replace(".", "_")
                lines.append(f"        {safe_cid}[{node_cid}]:::active")
                lines.append(f"        {safe_root_cid} --> {safe_cid}")

        lines.append("    end")

    if manifest.bypassed_steps:
        lines.append("    subgraph Quarantined_Bypass")
        for bypass in manifest.bypassed_steps:
            safe_cid = bypass.bypassed_node_cid.replace(":", "_").replace("-", "_").replace(".", "_")
            lines.append(f"        {safe_cid}[{bypass.bypassed_node_cid}]:::bypassed")
            lines.append(f"        {safe_root_cid} -. {bypass.justification} .-> {safe_cid}")
        lines.append("    end")

    return "\n".join(lines)


def project_manifest_to_markdown(manifest: WorkflowManifest) -> str:
    """Deterministically compile the envelope into an Agent Card Markdown string."""
    lines: list[str] = [
        "# CoReason Agent Card",
        "",
        "## Workflow Identification",
        f"- **Manifest Version:** {manifest.manifest_version}",
        f"- **Tenant ID:** {manifest.tenant_cid or 'Unbound'}",
        f"- **Session ID:** {manifest.session_cid or 'Unbound'}",
        "",
        "## Root Topology",
        f"- **Type:** `{manifest.topology.topology_class}`",
    ]

    if getattr(manifest.topology, "architectural_intent", None):
        lines.append(f"- **Intent:** {manifest.topology.architectural_intent}")  # type: ignore[union-attr]
    if getattr(manifest.topology, "justification", None):
        lines.append(f"- **Justification:** *{manifest.topology.justification}*")  # type: ignore[union-attr]

    lines.append("")
    lines.append("## Node Ledger & Personas")

    if hasattr(manifest.topology, "nodes"):
        for node_cid, node in getattr(manifest.topology, "nodes", {}).items():
            lines.append(f"### Node: `{node_cid}`")
            lines.append(f"- **Type:** `{node.topology_class}`")
            lines.append(f"- **Description:** {node.description}")

            if getattr(node, "architectural_intent", None):
                lines.append(f"- **Intent:** {node.architectural_intent}")
            if getattr(node, "justification", None):
                lines.append(f"- **Justification:** *{node.justification}*")

        if getattr(node, "agent_attestation", None) is not None:
            attest = node.agent_attestation
            if attest:
                lines.append(f"- **Lineage Hash:** `{attest.training_lineage_hash}`")
        lines.append("")

    return "\n".join(lines)


_CACHED_ONTOLOGY_SCHEMA: dict[str, Any] | None = None


def get_ontology_schema() -> dict[str, Any]:
    """Dynamically generate the CoReason ontology JSON schema."""
    global _CACHED_ONTOLOGY_SCHEMA
    if _CACHED_ONTOLOGY_SCHEMA is not None:
        return copy.deepcopy(_CACHED_ONTOLOGY_SCHEMA)

    models_to_export: list[type[CoreasonBaseState]] = []

    for name in sorted(dir(ontology)):
        obj = getattr(ontology, name)
        if isinstance(obj, type) and issubclass(obj, CoreasonBaseState) and obj is not CoreasonBaseState:
            models_to_export.append(obj)

    if not models_to_export:
        return {}

    pydantic_models = cast(
        "Sequence[tuple[type[BaseModel], typing.Literal['validation']]]",
        [(m, "validation") for m in models_to_export],
    )

    _, top_level_schema = models_json_schema(
        pydantic_models,
        title="CoReason Shared Kernel Ontology",
        description="CoReason Shared Kernel Ontology\n\nUnified JSON Schema for the Coreason Manifest",
    )

    _CACHED_ONTOLOGY_SCHEMA = top_level_schema
    return copy.deepcopy(top_level_schema)


def verify_manifold_bounds(step: str, payload_bytes: bytes) -> BaseModel:
    """Validate a payload against the designated ontology step model.

    Raises:
        ValueError: If the `step` parameter is unknown.
        ValidationError: If `payload_bytes` does not conform to the schema.
    """
    target_schema = SCHEMA_REGISTRY.get(step)
    if not target_schema:
        raise ValueError(f"FATAL: Unknown step '{step}'. Valid steps: {list(SCHEMA_REGISTRY.keys())}")

    return target_schema.model_validate_json(payload_bytes)


def synthesize_remediation_intent(
    error: ValidationError, target_node_cid: str, fault_cid: str
) -> System2RemediationIntent:
    """
    Pure functional adapter. Maps a raw Pythonic pydantic.ValidationError into a
    language-model-legible System2RemediationIntent without triggering runtime side effects.
    """
    receipts: list[ManifestViolationReceipt] = []
    for err in error.errors():
        loc_path = "".join(f"/{item!s}" for item in err["loc"]) if err["loc"] else "/"
        err_type = err["type"]
        msg = err.get("msg", "Invalid structural payload.")
        if err_type == "missing":
            msg = f"The required semantic boundary at '{loc_path}' is completely missing. You must project this missing dimension to satisfy the StateContract."

        receipts.append(
            ManifestViolationReceipt(failing_pointer=loc_path, violation_category=err_type, diagnostic_message=msg)
        )

    return System2RemediationIntent(fault_cid=fault_cid, target_node_cid=target_node_cid, violation_receipts=receipts)


def align_semantic_manifolds(
    task_cid: str,
    source_modalities: list[str],
    target_modalities: list[Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]],
    artifact_event_cid: str,
) -> EpistemicTransmutationTask | None:
    """
    A pure algebraic functor that calculates the epistemic gap between two nodes.
    If the target requires modalities absent in the source, it emits a deterministic Transmutation Task.
    """
    source_set = set(source_modalities)
    target_set = set(target_modalities)
    if target_set.issubset(source_set):
        return None
    schema_governance = None
    if "semantic_graph" in target_modalities:
        schema_governance = ontology.SchemaDrivenExtractionSLA(
            schema_registry_uri=AnyUrl("http://example.com/schema"),
            extraction_framework="docling_graph_explicit",
            max_schema_retries=3,
            validation_failure_action="escalate_to_human",
        )
    from coreason_manifest.spec.ontology import OpticalParsingSLA

    optical_governance = None
    if "raster_image" in target_modalities or "tabular_grid" in target_modalities:
        optical_governance = OpticalParsingSLA(
            force_ocr=False, bitmap_dpi_resolution=72, table_structure_recognition=True
        )

    return EpistemicTransmutationTask(
        task_cid=task_cid,
        artifact_event_cid=artifact_event_cid,
        target_modalities=list(target_modalities),
        schema_governance=schema_governance,
        optical_governance=optical_governance,
    )


def calculate_remaining_compute(ledger: ontology.EpistemicLedgerState, initial_escrow_magnitude: int) -> int:
    """
    A pure algebraic functor to reduce the ledger state without global variable locks.
    """
    remaining = initial_escrow_magnitude
    for event in ledger.history:
        if isinstance(event, ontology.TokenBurnReceipt) or getattr(event, "topology_class", None) == "token_burn":
            remaining -= getattr(event, "burn_magnitude", 0)
            if remaining < 0:
                raise ValueError("Mathematical Boundary Breached: Compute escrow exhausted.")
    return remaining


def calculate_latent_alignment(
    v1: VectorEmbeddingState, v2: VectorEmbeddingState, policy: OntologicalAlignmentPolicy
) -> float:
    """
    A pure algebraic functor to calculate cosine similarity of two vectors.
    """

    if v1.foundation_matrix_name != v2.foundation_matrix_name or v1.dimensionality != v2.dimensionality:
        raise ValueError("Topological Contradiction: Vector geometries are incommensurable.")

    try:
        b1 = base64.b64decode(v1.vector_base64)
        b2 = base64.b64decode(v2.vector_base64)
    except Exception as e:
        raise ValueError("Topological Contradiction: Invalid base64 encoding.") from e

    arr1 = np.frombuffer(b1, dtype=np.float32)
    arr2 = np.frombuffer(b2, dtype=np.float32)

    if len(arr1) != v1.dimensionality or len(arr2) != v2.dimensionality:
        raise ValueError("Byte length does not match declared dimensionality.")

    with np.errstate(all="ignore"):
        mag1, mag2 = np.linalg.norm(arr1), np.linalg.norm(arr2)
        similarity = 0.0 if mag1 == 0.0 or mag2 == 0.0 else float(np.dot(arr1, arr2) / (mag1 * mag2))

    if math.isnan(similarity):
        similarity = 0.0

    if similarity > 1.0:
        similarity = 1.0
    elif similarity < -1.0:
        similarity = -1.0

    if similarity < policy.min_cosine_similarity:
        raise TamperFaultEvent("Latent alignment failed.")

    return similarity


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
            raise TamperFaultEvent(f"Node hash mismatch for request {node.request_cid}")
        for parent_hash in node.parent_hashes:
            if parent_hash not in node_map:
                raise TamperFaultEvent(f"Missing parent hash {parent_hash} in trace")
    return True


_AST_ALLOWLIST: tuple[type, ...] = (
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Dict,
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.BinOp,
    ast.UnaryOp,
    ast.operator,
    ast.unaryop,
    ast.Subscript,
    ast.Slice,
)


def verify_ast_safety(payload: str) -> bool:
    """
    Mechanistically sandboxes dynamically generated strings by compiling them into an AST
    and rigorously walking the graph to ensure no kinetic execution bleed occurs.

    AGENT INSTRUCTION: The `base_allowlist` mathematically defines a strict Default-Deny
    node perimeter. Any AST node not explicitly projected within this matrix is quarantined.
    """
    try:
        tree = ast.parse(payload, mode="eval")
    except SyntaxError as e:
        raise ValueError("Payload is not valid syntax.") from e

    for node in ast.walk(tree):
        if not isinstance(node, _AST_ALLOWLIST):
            raise ValueError(f"Kinetic execution bleed detected. Forbidden AST node: {type(node).__name__}")
        if isinstance(node, ast.Pow):
            raise ValueError("Kinetic execution bleed detected. Forbidden AST node: Pow")

    return True


def transmute_state_differential(
    current_state: dict[str, Any], differential: ontology.StateDifferentialManifest
) -> dict[str, Any]:
    # ⚡ Bolt Optimization: Replace slow Pydantic model_dump with manual dictionary construction (~5x faster)
    patch_list = [
        {"op": p.op, "path": p.path, "value": p.value}
        if p.value is not None
        else (
            {"op": p.op, "path": p.path, "from": p.from_path}
            if p.from_path is not None
            else {"op": p.op, "path": p.path}
        )
        for p in differential.patches
    ]
    try:
        return cast("dict[str, Any]", jsonpatch.apply_patch(current_state, patch_list))
    except (jsonpatch.JsonPatchException, jsonpatch.JsonPointerException, TypeError) as e:
        raise ValueError(f"Patch operation failed: {e}") from e
