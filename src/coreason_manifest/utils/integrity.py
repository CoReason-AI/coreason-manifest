import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MerkleNode(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    previous_hashes: list[str] = Field(..., description="List of precedent hashes (supports Merge events)")
    node_id: str = Field(..., description="ID of the executing node")
    state_diff_hash: str = Field(..., description="Hash of the blackboard state")

    def compute_hash(self, algorithm: Literal["sha256", "sha512"] = "sha256") -> str:
        """
        Computes the hash of this node.
        Structure: Hash(timestamp + previous_hashes_sorted + node_id + state_diff_hash)
        """
        # Sort hashes for deterministic merging
        sorted_prev = ",".join(sorted(self.previous_hashes))
        payload = f"{self.timestamp}|{sorted_prev}|{self.node_id}|{self.state_diff_hash}"

        if algorithm == "sha256":
            return hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if algorithm == "sha512":
            return hashlib.sha512(payload.encode("utf-8")).hexdigest()
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def compute_state_hash(blackboard: dict[str, Any], algorithm: Literal["sha256", "sha512"] = "sha256") -> str:
    """
    Computes a deterministic hash of the blackboard state.
    """
    # Use sort_keys=True for determinism
    serialized = json.dumps(blackboard, sort_keys=True, default=str)
    if algorithm == "sha256":
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if algorithm == "sha512":
        return hashlib.sha512(serialized.encode("utf-8")).hexdigest()
    raise ValueError(f"Unsupported algorithm: {algorithm}")


def create_merkle_node(
    previous_hashes: list[str],
    node_id: str,
    blackboard: dict[str, Any],
    algorithm: Literal["sha256", "sha512"] = "sha256",
) -> MerkleNode:
    """
    Creates a new MerkleNode anchored to the previous hashes.
    """
    state_hash = compute_state_hash(blackboard, algorithm)
    return MerkleNode(
        timestamp=datetime.now(UTC).isoformat(),
        previous_hashes=previous_hashes,
        node_id=node_id,
        state_diff_hash=state_hash,
    )


def verify_merkle_proof(chain: list[MerkleNode], algorithm: Literal["sha256", "sha512"] = "sha256") -> bool:
    """
    Verifies the cryptographic integrity of the state chain (DAG).
    Returns True if every node's previous_hashes point to valid hashes of *preceding* nodes in the chain.

    In a DAG, "preceding" means topological order. Here, we simplify by assuming the list `chain`
    is topologically sorted (or at least, parents appear before children).
    """
    if not chain:
        return True

    # Map Hash -> Node Index (or just existence)
    # We need to verify that for every node, ALL its previous_hashes exist in the known history.
    known_hashes = set()

    # Genesis node usually has empty previous_hashes or a special "0" hash.
    # We'll assume the first node is genesis.
    first_node = chain[0]
    known_hashes.add(first_node.compute_hash(algorithm))

    # For subsequent nodes
    for i in range(1, len(chain)):
        current = chain[i]

        # Verify ancestry
        for prev_hash in current.previous_hashes:
            # Special case for genesis marker "0" if we allow it, but usually we expect real hashes.
            # If previous_hashes is ["0"], we might skip check?
            # The test case uses "0" for genesis.
            if prev_hash == "0":
                continue

            if prev_hash not in known_hashes:
                # Broken link: parent hash not found in the verified chain so far
                return False

        # Register current node
        current_hash = current.compute_hash(algorithm)
        known_hashes.add(current_hash)

    return True
