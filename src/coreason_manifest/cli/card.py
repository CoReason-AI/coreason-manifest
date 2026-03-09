# Copyright (c) 2026 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This module is a purely stateless compiler.
It translates a mathematically bounded WorkflowEnvelope into a 1D Markdown projection.
It must not execute any agent logic, connect to remote sockets, or utilize Jinja2."""

import argparse
import sys
from pathlib import Path

from pydantic import TypeAdapter

from coreason_manifest.workflow.envelope import WorkflowEnvelope


def project_envelope_to_markdown(envelope: WorkflowEnvelope) -> str:
    """Deterministically compile the envelope into an Agent Card Markdown string."""
    lines: list[str] = [
        "# CoReason Agent Card",
        "",
        "## Workflow Identification",
        f"- **Manifest Version:** {envelope.manifest_version}",
        f"- **Tenant ID:** {envelope.tenant_id or 'Unbound'}",
        f"- **Session ID:** {envelope.session_id or 'Unbound'}",
        "",
        "## Root Topology",
        f"- **Type:** `{envelope.topology.type}`",
    ]

    architectural_intent = getattr(envelope.topology, "architectural_intent", None)
    if architectural_intent:
        lines.append(f"- **Intent:** {architectural_intent}")

    justification = getattr(envelope.topology, "justification", None)
    if justification:
        lines.append(f"- **Justification:** *{justification}*")

    lines.append("")
    lines.append("## Node Ledger & Personas")

    nodes = getattr(envelope.topology, "nodes", {})
    for node_id, node in nodes.items():
        lines.append(f"### Node: `{node_id}`")
        lines.append(f"- **Type:** `{node.type}`")
        lines.append(f"- **Description:** {node.description}")

        if node.architectural_intent:
            lines.append(f"- **Intent:** {node.architectural_intent}")
        if node.justification:
            lines.append(f"- **Justification:** *{node.justification}*")

        if getattr(node, "agent_attestation", None) is not None:
            attest = node.agent_attestation
            if attest:
                lines.append(f"- **Lineage Hash:** `{attest.training_lineage_hash}`")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic Markdown visualizer for Workflow Envelopes.")
    parser.add_argument("payload", type=Path, help="Path to the JSON workflow envelope.")
    args = parser.parse_args()

    if not args.payload.exists():
        sys.stderr.write(f"Error: File {args.payload} not found.\n")
        sys.exit(1)

    try:
        payload_bytes = args.payload.read_bytes()
        adapter = TypeAdapter(WorkflowEnvelope)
        manifest = adapter.validate_json(payload_bytes)

        markdown_string = project_envelope_to_markdown(manifest)
        sys.stdout.write(markdown_string + "\n")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"Envelope Validation Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
