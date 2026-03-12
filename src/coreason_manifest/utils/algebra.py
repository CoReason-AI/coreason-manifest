# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This module contains pure data transformations of the Hollow Data Plane."""

import ast
import base64
import copy
import hashlib
import math
import struct
import typing
from collections.abc import Sequence
from typing import Any, Literal, cast

from pydantic import BaseModel, ValidationError
from pydantic.json_schema import models_json_schema

import coreason_manifest.spec.ontology as ontology
from coreason_manifest.spec.ontology import (
    AnyTopologyManifest,
    CognitiveStateProfile,
    CoreasonBaseState,
    DocumentLayoutManifest,
    DynamicRoutingManifest,
    EpistemicCompressionSLA,
    EpistemicTransmutationTask,
    ExecutionNodeReceipt,
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
}


def project_manifest_to_mermaid(manifest: DynamicRoutingManifest) -> str:
    """Deterministically compile the routing manifest into a Mermaid.js directed graph."""
    lines: list[str] = [
        "graph TD",
        "    classDef active fill:#e1f5fe,stroke:#333,stroke-width:2px;",
        "    classDef bypassed fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5;",
    ]

    safe_root_id = manifest.manifest_id.replace(":", "_").replace("-", "_").replace(".", "_")
    lines.append(f"    {safe_root_id}[{manifest.manifest_id}]")

    for modality in manifest.artifact_profile.detected_modalities:
        lines.append(f"    subgraph {modality}")

        if modality in manifest.active_subgraphs:
            for node_id in manifest.active_subgraphs[modality]:
                safe_id = node_id.replace(":", "_").replace("-", "_").replace(".", "_")
                lines.append(f"        {safe_id}[{node_id}]:::active")
                lines.append(f"        {safe_root_id} --> {safe_id}")

        lines.append("    end")

    if manifest.bypassed_steps:
        lines.append("    subgraph Quarantined_Bypass")
        for bypass in manifest.bypassed_steps:
            safe_id = bypass.bypassed_node_id.replace(":", "_").replace("-", "_").replace(".", "_")
            lines.append(f"        {safe_id}[{bypass.bypassed_node_id}]:::bypassed")
            lines.append(f"        {safe_root_id} -. {bypass.justification} .-> {safe_id}")
        lines.append("    end")

    return "\n".join(lines)


def project_manifest_to_markdown(manifest: WorkflowManifest) -> str:
    """Deterministically compile the envelope into an Agent Card Markdown string."""
    lines: list[str] = [
        "# CoReason Agent Card",
        "",
        "## Workflow Identification",
        f"- **Manifest Version:** {manifest.manifest_version}",
        f"- **Tenant ID:** {manifest.tenant_id or 'Unbound'}",
        f"- **Session ID:** {manifest.session_id or 'Unbound'}",
        "",
        "## Root Topology",
        f"- **Type:** `{manifest.topology.type}`",
    ]

    if getattr(manifest.topology, "architectural_intent", None):
        lines.append(f"- **Intent:** {manifest.topology.architectural_intent}")  # type: ignore[union-attr]
    if getattr(manifest.topology, "justification", None):
        lines.append(f"- **Justification:** *{manifest.topology.justification}*")  # type: ignore[union-attr]

    lines.append("")
    lines.append("## Node Ledger & Personas")

    if hasattr(manifest.topology, "nodes"):
        for node_id, node in getattr(manifest.topology, "nodes", {}).items():
            lines.append(f"### Node: `{node_id}`")
            lines.append(f"- **Type:** `{node.type}`")
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


def get_ontology_schema() -> dict[str, Any]:
    """Dynamically generate the CoReason ontology JSON schema."""
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

    return top_level_schema


def validate_payload(step: str, payload_bytes: bytes) -> BaseModel:
    """Validate a payload against the designated ontology step model.

    Raises:
        ValueError: If the `step` parameter is unknown.
        ValidationError: If `payload_bytes` does not conform to the schema.
    """
    target_schema = SCHEMA_REGISTRY.get(step)
    if not target_schema:
        raise ValueError(f"FATAL: Unknown step '{step}'. Valid steps: {list(SCHEMA_REGISTRY.keys())}")

    return target_schema.model_validate_json(payload_bytes)


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


def calculate_remaining_compute(ledger: ontology.EpistemicLedgerState, initial_escrow_magnitude: int) -> int:
    """
    A pure algebraic functor to reduce the ledger state without global variable locks.
    """
    remaining = initial_escrow_magnitude
    for event in ledger.history:
        if isinstance(event, ontology.TokenBurnReceipt) or getattr(event, "type", None) == "token_burn":
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
    if v1.model_name != v2.model_name or v1.dimensionality != v2.dimensionality:
        raise ValueError("Topological Contradiction: Vector geometries are incommensurable.")

    b1 = base64.b64decode(v1.vector_base64)
    b2 = base64.b64decode(v2.vector_base64)

    try:
        vec1 = struct.unpack(f"<{v1.dimensionality}f", b1)
        vec2 = struct.unpack(f"<{v2.dimensionality}f", b2)
    except struct.error as e:
        raise ValueError("Byte length does not match declared dimensionality.") from e

    dot_product = math.fsum(a * b for a, b in zip(vec1, vec2, strict=True))
    mag1 = math.sqrt(math.fsum(x * x for x in vec1))
    mag2 = math.sqrt(math.fsum(x * x for x in vec2))

    similarity = 0.0 if mag1 == 0 or mag2 == 0 else dot_product / (mag1 * mag2)

    if similarity < policy.min_cosine_similarity:
        raise ValueError("TamperFaultEvent: Latent alignment failed.")

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
            raise TamperFaultEvent(f"Node hash mismatch for request {node.request_id}")
        for parent_hash in node.parent_hashes:
            if parent_hash not in node_map:
                raise TamperFaultEvent(f"Missing parent hash {parent_hash} in trace")
    return True


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

    base_allowlist = [
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
    ]

    if hasattr(ast, "Index"):
        base_allowlist.append(ast.Index)
    if hasattr(ast, "Slice"):
        base_allowlist.append(ast.Slice)

    allowlist: tuple[type, ...] = tuple(base_allowlist)

    for node in ast.walk(tree):
        if not isinstance(node, allowlist):
            raise ValueError(f"Kinetic execution bleed detected. Forbidden AST node: {type(node).__name__}")

    return True


def apply_state_differential(
    current_state: dict[str, Any], manifest: ontology.StateDifferentialManifest
) -> dict[str, Any]:
    """
    A pure mathematical functor to apply an RFC 6902 JSON patch without mutating the input dictionary.
    """
    new_state = copy.deepcopy(current_state)

    for patch in manifest.patches:
        path = patch.path
        if not path.startswith("/"):
            if path == "":
                if patch.op == "test":
                    if new_state != patch.value:
                        raise ValueError("Patch test operation failed.")
                    continue
                raise ValueError(f"Invalid path or root operation not supported: {path}")
            raise ValueError(f"Invalid JSON pointer: {path}")

        parts = [p.replace("~1", "/").replace("~0", "~") for p in path.split("/")[1:]]

        target: Any = new_state
        for part in parts[:-1]:
            if isinstance(target, dict):
                if part not in target:
                    raise ValueError(f"Invalid path: {path}")
                target = target[part]
            elif isinstance(target, list):
                try:
                    idx = int(part)
                    target = target[idx]
                except (ValueError, IndexError) as e:
                    raise ValueError(f"Invalid path: {path}") from e
            else:
                raise ValueError(f"Invalid path: {path}")

        last_part = parts[-1]

        def resolve_from_path(from_path: str) -> tuple[Any, Any]:
            if not isinstance(from_path, str) or not from_path.startswith("/"):
                raise ValueError(f"Invalid from_path: {from_path}")

            from_parts = [p.replace("~1", "/").replace("~0", "~") for p in from_path.split("/")[1:]]
            from_target: Any = new_state
            for part in from_parts[:-1]:
                if isinstance(from_target, dict):
                    if part not in from_target:
                        raise ValueError(f"Invalid from_path: {from_path}")
                    from_target = from_target[part]
                elif isinstance(from_target, list):
                    try:
                        idx = int(part)
                        from_target = from_target[idx]
                    except (ValueError, IndexError) as e:
                        raise ValueError(f"Invalid from_path: {from_path}") from e
                else:
                    raise ValueError(f"Invalid from_path: {from_path}")

            from_last = from_parts[-1]
            return from_target, from_last

        def extract_from_target(t: Any, key: str) -> Any:
            if isinstance(t, dict):
                if key not in t:
                    raise ValueError("Key not found")
                return t[key]
            if isinstance(t, list):
                if key == "-":
                    raise ValueError("Cannot extract from end of array")
                try:
                    idx = int(key)
                    if idx < 0 or idx >= len(t):
                        raise ValueError("Index out of bounds")
                    return t[idx]
                except ValueError as e:
                    raise ValueError("Invalid index") from e
            raise ValueError("Target is not dict or list")

        def ablate_from_target(t: Any, key: str) -> None:
            if isinstance(t, dict):
                if key not in t:
                    raise ValueError("Key not found")
                del t[key]
            elif isinstance(t, list):
                if key == "-":
                    raise ValueError("Cannot remove from end of array")
                try:
                    idx = int(key)
                    if idx < 0 or idx >= len(t):
                        raise ValueError("Index out of bounds")
                    t.pop(idx)
                except ValueError as e:
                    raise ValueError("Invalid index") from e

        if patch.op == "add":
            if isinstance(target, dict):
                target[last_part] = patch.value
            elif isinstance(target, list):
                if last_part == "-":
                    target.append(patch.value)
                else:
                    try:
                        idx = int(last_part)
                        if idx < 0 or idx > len(target):
                            raise ValueError(f"Index out of bounds: {path}")
                        target.insert(idx, patch.value)
                    except ValueError as e:
                        raise ValueError(f"Invalid index: {last_part}") from e
            else:
                raise ValueError(f"Cannot add to path: {path}")

        elif patch.op == "remove":
            try:
                ablate_from_target(target, last_part)
            except ValueError as e:
                raise ValueError(f"Cannot remove from path {path}: {e}") from e

        elif patch.op == "replace":
            try:
                extract_from_target(target, last_part)

                if isinstance(target, dict):
                    target[last_part] = patch.value
                elif isinstance(target, list):
                    if last_part == "-":
                        raise ValueError("Cannot replace at end of array")
                    idx = int(last_part)
                    target[idx] = patch.value
            except ValueError as e:
                raise ValueError(f"Cannot replace at path {path}: {e}") from e

        elif patch.op in ("copy", "move"):
            from_path = patch.value
            if not isinstance(from_path, str):
                raise ValueError(f"Invalid from_path: {from_path}")
            try:
                from_target, from_last = resolve_from_path(from_path)
                val = extract_from_target(from_target, from_last)
                if patch.op == "move":
                    ablate_from_target(from_target, from_last)
                if patch.op == "copy":
                    val = copy.deepcopy(val)
            except ValueError as e:
                raise ValueError(f"Invalid from_path operation: {e}") from e

            if isinstance(target, dict):
                target[last_part] = val
            elif isinstance(target, list):
                if last_part == "-":
                    target.append(val)
                else:
                    try:
                        idx = int(last_part)
                        if idx < 0 or idx > len(target):
                            raise ValueError(f"Index out of bounds: {path}")
                        target.insert(idx, val)
                    except ValueError as e:
                        raise ValueError(f"Invalid index: {last_part}") from e
            else:
                raise ValueError(f"Cannot copy/move to path: {path}")

        elif patch.op == "test":
            try:
                current_val = extract_from_target(target, last_part)
                if current_val != patch.value:
                    raise ValueError("Patch test operation failed.")
            except ValueError as e:
                if "Patch test operation failed" in str(e):
                    raise
                raise ValueError("Patch test operation failed.") from e

    return new_state
