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
        description="The W3C DID of the trusted authority that cryptographically signed the credential."
    )
    cryptographic_proof_blob: str = Field(
        description="The base64-encoded SD-JWT or ZK-SNARK proving the claims without revealing the private key."
    )
    authorization_claims: dict[str, Any] = Field(
        description="The strict, domain-agnostic JSON dictionary of predicates being proven (e.g., {'clearance': 'RESTRICTED'})."
    )
