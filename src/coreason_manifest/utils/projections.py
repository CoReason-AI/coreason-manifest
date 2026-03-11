# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This module contains pure data transformations of the Hollow Data Plane."""

import typing
from collections.abc import Sequence
from typing import Any, cast

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

import coreason_manifest
from coreason_manifest.spec.ontology import (
    CognitiveStateProfile,
    CoreasonBaseModel,
    DocumentLayoutManifest,
    DynamicRoutingManifest,
    StateMutationIntent,
    System2RemediationIntent,
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
    models_to_export: list[type[CoreasonBaseModel]] = []

    for name in sorted(set(coreason_manifest.__all__)):
        obj = getattr(coreason_manifest, name, None)
        if isinstance(obj, type) and issubclass(obj, CoreasonBaseModel) and obj is not CoreasonBaseModel:
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
        description="Unified JSON Schema for the Coreason Manifest",
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
