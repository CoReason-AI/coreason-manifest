# src/coreason_manifest/utils/integrity.py

import hashlib
import json
import math
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Any, TypedDict, cast

from pydantic import BaseModel, Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.contracts import AtomicSkill, StrictJsonDict


def to_canonical_timestamp(dt: datetime) -> str:
    """
    Converts a datetime to a strict UTC string format: YYYY-MM-DDTHH:MM:SSZ
    """
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=UTC)

    # Convert to UTC
    dt_utc = dt.astimezone(UTC)

    # Format as YYYY-MM-DDTHH:MM:SSZ (no microseconds)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


class MerkleNode(TypedDict):
    """
    Standard structure for verifiable execution blocks.
    """

    execution_hash: str
    parent_hashes: list[str]


class HashingStrategy(ABC):
    """
    Abstract base class for hashing strategies.
    Ensures verification capability across different protocol versions.
    """

    @abstractmethod
    def compute_hash(self, obj: Any) -> str:
        """Computes the deterministic hash of the object."""


class CanonicalHashingStrategy(HashingStrategy):
    """
    Canonical hashing strategy enforcing RFC 8785 compliance.
    """

    def _recursive_sort_and_sanitize(self, obj: Any, is_root: bool = False) -> Any:
        """
        Prepares an object for RFC 8785 Canonical JSON serialization.

        SOTA Fix: Only exclude hash/signature keys at the root level to prevent
        'hash smuggling' vulnerabilities.
        """
        if isinstance(obj, dict):
            # Define excluded keys only if we are at the root level
            excluded_keys = {"execution_hash", "signature", "annotations"} if is_root else set()

            return {
                k: self._recursive_sort_and_sanitize(v, is_root=False)
                for k, v in sorted(obj.items())
                if k not in excluded_keys
            }
        if isinstance(obj, (list, tuple)):
            return [self._recursive_sort_and_sanitize(x, is_root=False) for x in obj]
        if isinstance(obj, (set, frozenset)):
            # Sets should be sorted lists
            return sorted([self._recursive_sort_and_sanitize(x, is_root=False) for x in obj], key=str)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return to_canonical_timestamp(obj)
        if isinstance(obj, BaseModel):
            # SOTA Fix: Use mode='json' to flatten Enums and complex types to primitives
            # BEFORE sorting, preventing "Object of type Enum is not JSON serializable" crashes.
            data = obj.model_dump(mode="json")
            return self._recursive_sort_and_sanitize(data, is_root=is_root)

        if hasattr(obj, "model_dump"):
            # Pydantic v2 or compatible
            return self._recursive_sort_and_sanitize(obj.model_dump(mode="json"), is_root=is_root)

        if isinstance(obj, float):
            if not math.isfinite(obj):
                raise ValueError("NaN and Infinity are not allowed in Canonical JSON")
            return obj

        if isinstance(obj, (int, str, bool)) or obj is None:
            return obj

        raise TypeError(f"Object of type {type(obj)} is not deterministically serializable.")

    def compute_hash(self, obj: Any) -> str:
        if hasattr(obj, "compute_hash"):
            return str(obj.compute_hash())

        # Start recursion with is_root=True
        sanitized = self._recursive_sort_and_sanitize(obj, is_root=True)

        json_bytes = json.dumps(
            sanitized, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

        return hashlib.sha256(json_bytes).hexdigest()


def compute_hash(obj: Any) -> str:
    """
    Computes a SHA-256 hash of a JSON-serializable object using the CanonicalHashingStrategy (RFC 8785).
    """
    return CanonicalHashingStrategy().compute_hash(obj)


class ProofOfTaskExecution(CoreasonModel):
    """
    Cryptographically signed receipt of task execution.
    Ties inputs, outputs, skill definition, and model weights to a Merkle node.
    """
    execution_id: str = Field(..., description="Unique ID of this execution.")
    timestamp: str = Field(..., description="UTC timestamp of execution.")
    skill: AtomicSkill = Field(..., description="The immutable skill executed.")
    inputs: StrictJsonDict = Field(..., description="Canonicalized inputs.")
    outputs: StrictJsonDict = Field(..., description="Canonicalized outputs.")
    model_weights_hash: str | None = Field(None, description="Hash of the model weights used, if applicable.")
    parent_hash: str | None = Field(None, description="Hash of the previous execution in the chain.")
    locked_status: bool = Field(True, description="Asserts that this step was locked/immutable.")

    # The self-hash of this object (excluding signature)
    execution_hash: str = Field(..., description="SHA-256 hash of the canonicalized fields.")
    signature: str | None = Field(None, description="Digital signature of the execution_hash.")


def generate_execution_receipt(
    execution_id: str,
    skill: AtomicSkill,
    inputs: StrictJsonDict,
    outputs: StrictJsonDict,
    parent_hash: str | None = None,
    model_weights_hash: str | None = None,
) -> ProofOfTaskExecution:
    """
    Generates a cryptographically verifiable receipt for a locked task execution.
    """
    # 1. Create the Payload Structure (without hash)
    # We use a temporary dict to compute hash
    payload = {
        "execution_id": execution_id,
        "timestamp": to_canonical_timestamp(datetime.now(UTC)),
        "skill": skill.model_dump(),
        "inputs": inputs,
        "outputs": outputs,
        "model_weights_hash": model_weights_hash,
        "parent_hash": parent_hash,
        "locked_status": True
    }

    # 2. Compute Canonical Hash
    strategy = CanonicalHashingStrategy()
    exec_hash = strategy.compute_hash(payload)

    # 3. Create PoTE Object
    return ProofOfTaskExecution(
        execution_id=cast(str, payload["execution_id"]),
        timestamp=cast(str, payload["timestamp"]),
        skill=skill,
        inputs=inputs,
        outputs=outputs,
        model_weights_hash=model_weights_hash,
        parent_hash=parent_hash,
        locked_status=True,
        execution_hash=exec_hash,
        signature=None
    )


def reconstruct_payload(node: Any) -> dict[str, Any]:
    """
    Reconstructs the payload dictionary used for hashing from a NodeExecution object.
    Automatically handles SOTA fields by using model_dump if available.
    """
    if isinstance(node, BaseModel):
        return node.model_dump()

    if isinstance(node, dict):
        return node

    # Strict Design Rule: No implicit casting.
    raise TypeError(f"Could not reconstruct payload from {type(node)}. Must be dict or Pydantic model.")


def verify_merkle_proof(
    trace: list[Any],
    trusted_root_hash: str | None = None,
    trusted_parent_hashes: set[str] | None = None,
) -> bool:
    """
    Verifies the cryptographic integrity of a DAG trace.
    Mathematically reconstructs the DAG topology to prove absence of parallel hallucinations.
    """
    if not trace:
        return False

    payloads = []

    # 1. Reconstruct payloads
    for node in trace:
        try:
            payload = reconstruct_payload(node)
            payloads.append(payload)
        except TypeError:
            return False

    # 2. Build Dependency Graph for Topological Sort
    nodes_by_hash = {}
    for p in payloads:
        h = p.get("execution_hash")
        if h:
            nodes_by_hash[h] = p

    adj_list = defaultdict(list)
    in_degree = defaultdict(int)

    for p in payloads:
        # Determine dependencies (parents)
        parent_hashes = p.get("parent_hashes", [])
        parent_hash = p.get("parent_hash")

        parents = set()
        if parent_hashes:
            parents.update(parent_hashes)
        if parent_hash:
            parents.add(parent_hash)

        # Only consider parents that are within the trace for sorting
        internal_parents = [pid for pid in parents if pid in nodes_by_hash]

        in_degree[id(p)] = len(internal_parents)

        for pid in internal_parents:
            adj_list[pid].append(p)

    # 3. Topological Sort (Kahn's Algorithm)
    queue = deque([p for p in payloads if in_degree[id(p)] == 0])
    sorted_trace = []

    while queue:
        node = queue.popleft()
        sorted_trace.append(node)

        node_hash = node.get("execution_hash")
        if node_hash and node_hash in adj_list:
            for child in adj_list[node_hash]:
                in_degree[id(child)] -= 1
                if in_degree[id(child)] == 0:
                    queue.append(child)

    if len(sorted_trace) != len(payloads):
        # Cycle detected
        return False

    # 4. Verification
    verified_hashes = set()

    for i, payload in enumerate(sorted_trace):
        # Verify Content Integrity
        computed_hash = compute_hash(payload)
        stored_hash = payload.get("execution_hash")

        if not stored_hash or stored_hash != computed_hash:
            return False

        # Verify Linkage
        parent_hashes = payload.get("parent_hashes", [])
        parent_hash = payload.get("parent_hash")

        expected_parents = set()
        if parent_hashes:
            expected_parents.update(parent_hashes)
        if parent_hash:
            expected_parents.add(parent_hash)

        if not expected_parents:
            # Genesis Node
            # SOTA Fix: Strict Genesis Validation.
            # If not expected parents (no parents declared), it MUST be the first node (i=0).
            # If i > 0, it's a floating/unlinked node injection attempt.
            if i > 0:
                return False

            if trusted_root_hash and stored_hash != trusted_root_hash:
                return False
        else:
            # Child Node: Every declared parent must be present in the VERIFIED pool or be the trusted root.
            for prev_hash in expected_parents:
                if trusted_root_hash and prev_hash == trusted_root_hash:
                    continue
                if trusted_parent_hashes and prev_hash in trusted_parent_hashes:
                    continue
                if prev_hash not in verified_hashes:
                    # Topology Violation: Node claims a parent that hasn't been verified.
                    return False

        # Add to verified set
        verified_hashes.add(stored_hash)

    return True
