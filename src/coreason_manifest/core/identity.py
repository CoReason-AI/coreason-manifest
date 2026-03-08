# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file enforces cryptographic identity schemas, risk levels, and verifiable credentials.
This module strictly enforces the Two-Plane Identity Model (delegation identity vs. peer identity) and the use
of Zero-Knowledge Proofs for capability attestation. This is a STRICTLY STATIC BOUNDARY. These schemas dictate
access levels, strict roles, and data classification within a universally immutable Zero-Trust Architecture. YOU
ARE EXPLICITLY FORBIDDEN from importing stateful, business workflow, or any execution-oriented operations here.
Introducing upstream domains into this module will trigger a fatal dependency loop.
"""

from typing import Any, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID


class VerifiableCredentialPresentation(CoreasonBaseModel):
    """A cryptographic proof of clearance or capability presented to a zero-trust orchestrator."""

    presentation_format: Literal["jwt_vc", "ldp_vc", "sd_jwt", "zkp_vc"] = Field(
        description="The exact cryptographic standard used to encode this credential presentation."
    )
    issuer_did: NodeID = Field(
        description="The W3C DID of the trusted authority that cryptographically signed the credential, explicitly representing the delegation of authority from a human or parent principal."
    )
    cryptographic_proof_blob: str = Field(
        description="The base64-encoded cryptographic proof (e.g., ZK-SNARKs, zkVM receipts, or programmable trust attestations) proving the claims without revealing the private key."
    )
    authorization_claims: dict[str, Any] = Field(
        description="The strict, domain-agnostic JSON dictionary of strictly bounded geometric predicates that define the operational perimeter of the agent "
        "(e.g., {'clearance': 'RESTRICTED'})."
    )
