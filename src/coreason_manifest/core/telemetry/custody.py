import hashlib
import json
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.core.telemetry.telemetry_schemas import AgentSignature, HardwareFingerprint


@runtime_checkable
class EpistemicEvent(Protocol):
    """
    Mock Protocol for EpistemicEvent being built by Epic 1.
    """
    event_id: str
    timestamp: float


@runtime_checkable
class EpistemicLedger(Protocol):
    """
    Mock Protocol for EpistemicLedger being built by Epic 1.
    """
    def append_event(self, event: EpistemicEvent) -> None:
        ...
    def get_history(self) -> list[EpistemicEvent]:
        ...


class MerkleHasher:
    """
    Cryptographic utility for tamper-proofing telemetry envelopes.
    """
    @staticmethod
    def compute_hash(agent_signature: AgentSignature, payload: Any, parent_envelope_hash: str | None) -> str:
        """
        Derive a SHA-256 hash from the agent signature, payload, and parent hash.
        This creates an unbroken, tamper-proof chain.
        """
        # Serialize components deterministically
        sig_dict = agent_signature.model_dump(mode="json")

        # Simple serialization for payload
        try:
            payload_str = json.dumps(payload, sort_keys=True)
        except (TypeError, ValueError):
            payload_str = str(payload)

        hasher = hashlib.sha256()
        hasher.update(json.dumps(sig_dict, sort_keys=True).encode("utf-8"))
        hasher.update(payload_str.encode("utf-8"))
        if parent_envelope_hash:
            hasher.update(parent_envelope_hash.encode("utf-8"))

        return hasher.hexdigest()


class EpistemicEnvelope(BaseModel):
    """
    Wraps a data payload in a cryptographically secure envelope, ensuring
    traceability back to the GPU hardware, model weights, and inference parameters.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    payload: Any = Field(..., description="The extracted data or proposition.")
    agent_signature: AgentSignature = Field(..., description="Agent and inference parameters.")
    hardware_fingerprint: HardwareFingerprint = Field(..., description="Compute and hardware specifics.")
    parent_envelope_hash: str | None = Field(None, description="Hash of the preceding envelope in the chain.")
    merkle_hash: str = Field(..., description="SHA-256 hash of this envelope's contents and parent hash.")
