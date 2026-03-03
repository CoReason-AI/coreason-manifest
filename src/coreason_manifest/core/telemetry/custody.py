import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.telemetry.telemetry_schemas import (
    AgentSignature,
    CryptographicSignature,
    HardwareFingerprint,
)


class EpistemicEnvelope(CoreasonModel):
    """
    Cryptographic wrapper for an epistemic event, enforcing strict Chain of Custody.
    """

    payload: Any = Field(..., description="The data payload of the epistemic event.")
    signature: CryptographicSignature | None = Field(default=None, description="Cryptographic signature.")
    hardware_fingerprint: HardwareFingerprint | None = Field(default=None, description="Hardware fingerprint.")
    agent_signature: AgentSignature | None = Field(default=None, description="Agent footprint.")
    parent_hash: str | None = Field(default=None, description="Hash of the preceding event.")


class MerkleHasher:
    """
    Computes a cryptographic Merkle hash of an EpistemicEnvelope.
    SOTA constraints: uses purely canonical serialization and injects boundary locks
    to prevent collision attacks.
    """

    @staticmethod
    def hash_envelope(envelope: EpistemicEnvelope) -> str:
        """
        Calculates the SHA-256 hash of the given EpistemicEnvelope safely.
        """
        hasher = hashlib.sha256()

        # Try canonical serialization of the payload
        try:
            if isinstance(envelope.payload, CoreasonModel):
                payload_bytes = envelope.payload.model_dump_json(exclude_none=True, by_alias=True).encode("utf-8")
            elif isinstance(envelope.payload, dict):
                # For basic dicts, just let json.dumps handle the sorting
                payload_bytes = json.dumps(
                    envelope.payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
                ).encode("utf-8")
            else:
                # Use standard Pydantic JSON dump
                payload_bytes = TypeAdapter(Any).dump_json(envelope.payload)
        except Exception as e:
            raise ValueError(f"Strict serialization failure. Cannot hash payload: {e}") from e

        # 1. Parent Hash
        if envelope.parent_hash:
            hasher.update(envelope.parent_hash.encode("utf-8"))
        hasher.update(b"\x00")

        # 2. Hardware Fingerprint
        if envelope.hardware_fingerprint:
            hasher.update(
                envelope.hardware_fingerprint.model_dump_json(exclude_none=True, by_alias=True).encode("utf-8")
            )
        hasher.update(b"\x00")

        # 3. Agent Signature
        if envelope.agent_signature:
            hasher.update(envelope.agent_signature.model_dump_json(exclude_none=True, by_alias=True).encode("utf-8"))
        hasher.update(b"\x00")

        # 4. Cryptographic Signature
        if envelope.signature:
            hasher.update(envelope.signature.model_dump_json(exclude_none=True, by_alias=True).encode("utf-8"))
        hasher.update(b"\x00")

        # 5. The Payload itself
        hasher.update(payload_bytes)

        return hasher.hexdigest()
