# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This module is a purely stateless Topological Compiler.
It translates a mathematically bounded DynamicRoutingManifest into a 2D Mermaid.js
projection. It must not execute any agent logic or connect to remote sockets."""

import argparse
import sys
from pathlib import Path

from pydantic import TypeAdapter

from coreason_manifest.spec.ontology import DynamicRoutingManifest


def project_manifest_to_mermaid(manifest: DynamicRoutingManifest) -> str:
    """Deterministically compile the routing manifest into a Mermaid.js directed graph."""
    lines: list[str] = [
        "graph TD",
        "    classDef active fill:#e1f5fe,stroke:#333,stroke-width:2px;",
        "    classDef bypassed fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5;",
    ]

    safe_root_id = manifest.manifest_id.replace(":", "_").replace("-", "_").replace(".", "_")
    lines.append(f"    {safe_root_id}[{manifest.manifest_id}]")

    # 1. Map Structural Modalities
    for modality in manifest.artifact_profile.detected_modalities:
        lines.append(f"    subgraph {modality}")

        # 2. Map Active Nodes
        if modality in manifest.active_subgraphs:
            for node_id in manifest.active_subgraphs[modality]:
                safe_id = node_id.replace(":", "_").replace("-", "_").replace(".", "_")
                lines.append(f"        {safe_id}[{node_id}]:::active")
                lines.append(f"        {safe_root_id} --> {safe_id}")

        lines.append("    end")

    # 3. Map Bypassed Steps
    if manifest.bypassed_steps:
        lines.append("    subgraph Quarantined_Bypass")
        for bypass in manifest.bypassed_steps:
            safe_id = bypass.bypassed_node_id.replace(":", "_").replace("-", "_").replace(".", "_")
            lines.append(f"        {safe_id}[{bypass.bypassed_node_id}]:::bypassed")
            lines.append(f"        {safe_root_id} -. {bypass.justification} .-> {safe_id}")
        lines.append("    end")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic Mermaid.js visualizer for Routing Manifests.")
    parser.add_argument("payload", type=Path, help="Path to the JSON routing manifest.")
    args = parser.parse_args()

    if not args.payload.exists():
        sys.stderr.write(f"Error: File {args.payload} not found.\n")
        sys.exit(1)

    try:
        payload_bytes = args.payload.read_bytes()
        adapter = TypeAdapter(DynamicRoutingManifest)
        manifest = adapter.validate_json(payload_bytes)

        mermaid_string = project_manifest_to_mermaid(manifest)
        sys.stdout.write(mermaid_string + "\n")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"Topological Validation Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
