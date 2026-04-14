# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any, cast
import msgspec  # type: ignore[import-not-found]
from coreason_manifest.spec.ontology import ExecutionEnvelopeState, MCPToolDefinition

def generate_lean4_mcp_tool() -> MCPToolDefinition:
    return MCPToolDefinition(
        name="verify_lean4_theorem",
        description="Use this tool to evaluate constructive mathematical proofs and universal invariants in Lean 4. Returns the verification status or the failing tactic state.",
        input_schema={
            "type": "object",
            "properties": {
                "formal_statement": {"type": "string", "maxLength": 100000},
                "tactic_proof": {"type": "string", "maxLength": 100000},
            },
            "required": ["formal_statement", "tactic_proof"],
        },
    )


def generate_clingo_mcp_tool() -> MCPToolDefinition:
    return MCPToolDefinition(
        name="execute_clingo_falsification",
        description="Use this tool to hunt for counter-models and evaluate NP-hard constraint satisfaction problems using Answer Set Programming (ASP).",
        input_schema={
            "type": "object",
            "properties": {
                "asp_program": {"type": "string", "maxLength": 65536},
                "max_models": {"type": "integer", "default": 1},
            },
            "required": ["asp_program"],
        },
    )


def generate_prolog_mcp_tool() -> MCPToolDefinition:
    return MCPToolDefinition(
        name="execute_prolog_deduction",
        description="Use this tool for evidentiary grounding, exact subgraph isomorphism, and traversing hierarchical knowledge bases via backward-chaining resolution.",
        input_schema={
            "type": "object",
            "properties": {"prolog_query": {"type": "string"}, "ephemeral_facts": {"type": "string"}},
            "required": ["prolog_query"],
        },
    )


class DeterministicTransportAdapter:
    """
    AGENT INSTRUCTION: Strictly serializes execution envelopes into deterministic JSON-RPC 2.0 bytes.

    CAUSAL AFFORDANCE: Operates as an impassable one-way serialization border. It physically strips mutable connection attributes to mathematically guarantee that all execution records are identical byte-for-byte across varying host environments.

    EPISTEMIC BOUNDS: It is natively forbidden from invoking socket writes, stdout, or async TCP loops. Pure structural projection relying entirely on `msgspec.json.Encoder(sort_keys=True)`.

    MCP ROUTING TRIGGERS: JSON-RPC 2.0, Byte Serialization, Zero-Trust Execution, msgspec, Deterministic Network Transport
    """

    @staticmethod
    def serialize_envelope(envelope: ExecutionEnvelopeState[Any]) -> bytes:
        payload_dict = envelope.model_dump(mode="json", exclude_none=True, by_alias=True)
        # Note: External Protocol Exemption. (JSON-RPC 2.0)
        wrapped_payload = {
            "jsonrpc": "2.0",
            "method": "coreason_execute",
            "params": payload_dict,
            "id": payload_dict.get("envelope_cid", "unknown"),
        }
        encoder = msgspec.json.Encoder(sort_keys=True)
        return cast(bytes, encoder.encode(wrapped_payload))
