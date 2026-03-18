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
    receipts: list[ManifestViolationReceipt] = []
    for err in error.errors():
        loc_path = "".join(f"/{item!s}" for item in err["loc"]) if err["loc"] else "/"
        err_type = err["type"]
        msg = err.get("msg", "Invalid structural payload.")
        if err_type == "missing":
            msg = f"The required semantic boundary at '{loc_path}' is completely missing. You must project this missing dimension to satisfy the StateContract."

        receipts.append(
            ManifestViolationReceipt(failing_pointer=loc_path, violation_type=err_type, diagnostic_message=msg)
        )

    return System2RemediationIntent(fault_id=fault_id, target_node_id=target_node_id, violation_receipts=receipts)


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

    try:
        dot_product = math.fsum(a * b for a, b in zip(vec1, vec2, strict=True))
        mag1_sq = math.fsum(x * x for x in vec1)
        mag2_sq = math.fsum(x * x for x in vec2)
    except (OverflowError, ValueError) as e:
        raise ValueError("Catastrophic loss of precision or overflow in vector calculation.") from e

    if (
        mag1_sq < 0
        or mag2_sq < 0
        or math.isinf(mag1_sq)
        or math.isinf(mag2_sq)
        or math.isnan(mag1_sq)
        or math.isnan(mag2_sq)
        or math.isinf(dot_product)
        or math.isnan(dot_product)
    ):
        raise ValueError("Catastrophic loss of precision or overflow in vector calculation.")

    mag1 = math.sqrt(mag1_sq)
    mag2 = math.sqrt(mag2_sq)

    similarity = 0.0 if mag1 == 0.0 or mag2 == 0.0 else dot_product / (mag1 * mag2)

    if math.isnan(similarity):
        similarity = 0.0

    # Float precision clamp
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

    base_allowlist.append(ast.Slice)

    allowlist: tuple[type, ...] = tuple(base_allowlist)

    for node in ast.walk(tree):
        if not isinstance(node, allowlist):
            raise ValueError(f"Kinetic execution bleed detected. Forbidden AST node: {type(node).__name__}")

    return True


def _resolve_from_path(new_state: Any, from_path: str) -> tuple[Any, Any]:
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


def _extract_from_target(t: Any, key: str) -> Any:
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


def _ablate_from_target(t: Any, key: str) -> None:
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


def _apply_patch_add(target: Any, last_part: str, value: Any) -> None:
    if isinstance(target, dict):
        target[last_part] = value
    elif isinstance(target, list):
        if last_part == "-":
            target.append(value)
        else:
            try:
                idx = int(last_part)
                if idx < 0 or idx > len(target):
                    raise ValueError(f"Index out of bounds: {last_part}")
                target.insert(idx, value)
            except ValueError as e:
                raise ValueError(f"Invalid index: {last_part}") from e
    else:
        raise ValueError(f"Cannot add to path: {last_part}")


def _apply_patch_remove(target: Any, last_part: str) -> None:
    try:
        _ablate_from_target(target, last_part)
    except ValueError as e:
        raise ValueError(f"Cannot remove from path: {e}") from e


def _apply_patch_replace(target: Any, last_part: str, value: Any) -> None:
    try:
        _extract_from_target(target, last_part)
        if isinstance(target, dict):
            target[last_part] = value
        elif isinstance(target, list):
            if last_part == "-":
                raise ValueError("Cannot replace at end of array")
            idx = int(last_part)
            target[idx] = value
    except ValueError as e:
        raise ValueError(f"{e}") from e


def _apply_patch_copy_move(new_state: Any, target: Any, last_part: str, patch: Any) -> None:
    from_path = patch.from_path
    if from_path is None:
        raise ValueError("from_path is mathematically required for copy/move operations.")

    if patch.path.startswith(from_path + "/"):
        raise ValueError(f"The 'from' location MUST NOT be a proper prefix of the 'path' location: {patch.path}")

    try:
        from_target, from_last = _resolve_from_path(new_state, from_path)
        val = _extract_from_target(from_target, from_last)
        if patch.op == "move":
            _ablate_from_target(from_target, from_last)
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

                if patch.op == "move" and from_target is target:
                    try:
                        from_idx = int(from_last)
                        if from_idx < int(last_part):
                            idx -= 1
                    except ValueError:
                        pass

                if idx < 0 or idx > len(target):
                    raise ValueError("Index out of bounds")
                target.insert(idx, val)
            except ValueError as e:
                raise ValueError(f"Invalid index: {last_part}") from e
    else:
        raise ValueError("Cannot copy/move to path")


def _apply_patch_test(target: Any, last_part: str, value: Any) -> None:
    try:
        current_val = _extract_from_target(target, last_part)
        if current_val != value:
            raise ValueError("Patch test operation failed.")
    except ValueError as e:
        if (
            "Patch test operation failed" in str(e)
            or "Index out of bounds" in str(e)
            or "Cannot extract from end of array" in str(e)
        ):
            raise
        raise ValueError("Patch test operation failed.") from e


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

        parts = []
        for p in path.split("/")[1:]:
            if "~" in p and not (p.endswith(("~0", "~1")) or "~0" in p or "~1" in p):
                raise ValueError(f"Invalid JSON pointer: {path}")
            parts.append(p.replace("~1", "/").replace("~0", "~"))

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

        patch_value = patch.value

        try:
            if patch.op == "add":
                _apply_patch_add(target, last_part, patch_value)
            elif patch.op == "remove":
                _apply_patch_remove(target, last_part)
            elif patch.op == "replace":
                _apply_patch_replace(target, last_part, patch_value)
            elif patch.op in ("copy", "move"):
                _apply_patch_copy_move(new_state, target, last_part, patch)
            elif patch.op == "test":
                _apply_patch_test(target, last_part, patch_value)
            else:
                raise ValueError(f"Unknown patch op: {patch.op}")
        except ValueError as e:
            # We preserve the original exception messaging strategy to not break any possible external test suite reliance on the exact strings in apply_state_differential.
            if (
                patch.op in ("remove", "replace")
                and "Patch test operation failed" not in str(e)
                and "Index out of bounds" not in str(e)
                and "Cannot extract from end of array" not in str(e)
            ):
                raise ValueError(f"Cannot {patch.op} at path {path}: {e}") from e
            if patch.op == "remove":
                # Special case, old code used from path: {e} and from path {path}: {e} for remove/replace.
                raise ValueError(f"Cannot remove from path {path}: {e}") from e
            if patch.op == "replace":
                raise ValueError(f"Cannot replace at path {path}: {e}") from e
            if patch.op in ("copy", "move"):
                # Exception was: raise ValueError(f"Cannot copy/move to path: {path}") from e or f"Index out of bounds: {path}"
                msg = str(e)
                if msg.startswith("Cannot copy/move to path"):
                    raise ValueError(f"Cannot copy/move to path: {path}") from e
                if msg.startswith("Index out of bounds"):
                    raise ValueError(f"Index out of bounds: {path}") from e
                raise
            if patch.op == "add":
                msg = str(e)
                if msg.startswith("Cannot add to path"):
                    raise ValueError(f"Cannot add to path: {path}") from e
                if msg.startswith("Index out of bounds"):
                    raise ValueError(f"Index out of bounds: {path}") from e
                raise
            raise

    return new_state
