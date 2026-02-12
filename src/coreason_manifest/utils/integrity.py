import hashlib
import json
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone

class MerkleNode(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    previous_hash: str = Field(..., description="Hash of the previous MerkleNode")
    node_id: str = Field(..., description="ID of the executing node")
    state_diff_hash: str = Field(..., description="Hash of the blackboard state")

    def compute_hash(self, algorithm: Literal["sha256", "sha512"] = "sha256") -> str:
        """
        Computes the hash of this node.
        Structure: Hash(timestamp + previous_hash + node_id + state_diff_hash)
        """
        payload = f"{self.timestamp}{self.previous_hash}{self.node_id}{self.state_diff_hash}"
        if algorithm == "sha256":
            return hashlib.sha256(payload.encode("utf-8")).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(payload.encode("utf-8")).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

def compute_state_hash(blackboard: dict[str, Any], algorithm: Literal["sha256", "sha512"] = "sha256") -> str:
    """
    Computes a deterministic hash of the blackboard state.
    """
    # Use sort_keys=True for determinism
    serialized = json.dumps(blackboard, sort_keys=True, default=str)
    if algorithm == "sha256":
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(serialized.encode("utf-8")).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

def create_merkle_node(
    previous_hash: str,
    node_id: str,
    blackboard: dict[str, Any],
    algorithm: Literal["sha256", "sha512"] = "sha256"
) -> MerkleNode:
    """
    Creates a new MerkleNode anchored to the previous hash.
    """
    state_hash = compute_state_hash(blackboard, algorithm)
    return MerkleNode(
        timestamp=datetime.now(timezone.utc).isoformat(),
        previous_hash=previous_hash,
        node_id=node_id,
        state_diff_hash=state_hash
    )

def verify_merkle_proof(chain: list[MerkleNode], algorithm: Literal["sha256", "sha512"] = "sha256") -> bool:
    """
    Verifies the cryptographic integrity of the state chain.
    Returns True if the chain is valid (every node's previous_hash matches the hash of the preceding node).
    """
    if not chain:
        return True

    # Iterate chain starting from second element
    for i in range(1, len(chain)):
        current = chain[i]
        prev = chain[i-1]

        # Check if current.previous_hash matches Hash(prev)
        expected_prev_hash = prev.compute_hash(algorithm)
        if current.previous_hash != expected_prev_hash:
            return False

    return True
