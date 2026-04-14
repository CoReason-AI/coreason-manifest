import time
import uuid

from authlib.jose import JoseError, jwt

from coreason_manifest.spec.mcp import MCPToolDefinition
from coreason_manifest.spec.ontology import (
    ConnectionSeveranceEvent,
    EpistemicSecurityProfile,
    FederatedHandshakeIntent,
)


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


class DecentralizedIdentityGateway:
    def __init__(self, security_profile: EpistemicSecurityProfile, trusted_issuers: dict[str, str]):
        self.security_profile = security_profile
        self.trusted_issuers = trusted_issuers

    def _trigger_instant_severance(self, target_id: str, reason: str):
        # We need event_cid and timestamp for ConnectionSeveranceEvent
        event = ConnectionSeveranceEvent(
            event_cid=str(uuid.uuid4()),
            timestamp=time.time(),
            target_ip_or_did=target_id,
            severance_reason=reason,
        )
        raise PermissionError(event.model_dump_json())

    def process_handshake(self, intent: FederatedHandshakeIntent) -> bool:
        issuer_did = intent.attestation.issuer_did

        # Gate 1 (DID Resolution)
        if issuer_did not in self.trusted_issuers:
            self._trigger_instant_severance(issuer_did, "did_resolution_failed")

        public_key = self.trusted_issuers[issuer_did]

        # Gate 2 (SD-JWT Verification)
        try:
            claims = jwt.decode(intent.attestation.sd_jwt_payload, public_key)
            claims.validate()
        except JoseError:
            self._trigger_instant_severance(issuer_did, "sd_jwt_tampered")

        # Gate 3 (PQC Interlock)
        if self.security_profile.epistemic_security == "CONFIDENTIAL" and intent.attestation.pqc_signature is None:
            self._trigger_instant_severance(issuer_did, "pqc_signature_invalid")

        return True
