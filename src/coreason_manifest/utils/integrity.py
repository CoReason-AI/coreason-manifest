# src/coreason_manifest/utils/integrity.py

import hashlib
import json
import math
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Any, TypedDict

from pydantic import BaseModel


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
    Strictly prohibits non-deterministic types.
    """

    def _recursive_sort_and_sanitize(self, obj: Any) -> Any:
        """
        Prepares an object for RFC 8785 Canonical JSON serialization.
        """
        if isinstance(obj, dict):
            # Recursively process values.
            # Strip any keys where the value is None.
            # Strip protected keys (execution_hash, signature, or keys starting with __).
            # Sort keys alphabetically to guarantee deterministic ordering.
            return {
                k: self._recursive_sort_and_sanitize(v)
                for k, v in sorted(obj.items())
                if v is not None and k not in {"execution_hash", "signature"} and not k.startswith("__")
            }

        if isinstance(obj, (list, tuple)):
            # Recursively process items.
            return [self._recursive_sort_and_sanitize(x) for x in obj]

        if isinstance(obj, (set, frozenset)):
            # Convert to sorted lists based on their string representation.
            return sorted([self._recursive_sort_and_sanitize(x) for x in obj], key=str)

        if isinstance(obj, uuid.UUID):
            # Convert to string via str(obj).
            return str(obj)

        if isinstance(obj, datetime):
            # Enforce conversion to UTC and format as a strict ISO-8601 string.
            return to_canonical_timestamp(obj)

        if isinstance(obj, BaseModel):
            # Use model_dump(exclude_none=True, mode="python") and recursively process.
            return self._recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, mode="python"))

        if isinstance(obj, float):
            # Allow finite floats. Explicitly raise a ValueError if math.isnan(obj) or math.isinf(obj).
            if math.isnan(obj) or math.isinf(obj):
                raise ValueError("NaN and Infinity are not allowed in Canonical JSON")
            return obj

        # Primitives (int, str, bool) & None: Return as-is.
        if isinstance(obj, (int, str, bool)) or obj is None:
            return obj

        # Strict Rejection (The Core Mandate)
        raise TypeError(f"Object of type {type(obj)} is not deterministically serializable.")

    def compute_hash(self, obj: Any) -> str:
        # 1. Pass the object through _recursive_sort_and_sanitize method.
        sanitized = self._recursive_sort_and_sanitize(obj)

        # 2. Serialize the sanitized output using json.dumps() with strict arguments.
        # sort_keys=True
        # ensure_ascii=False
        # separators=(",", ":")
        # allow_nan=False
        json_bytes = json.dumps(
            sanitized, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

        # 3. Returns the hashlib.sha256(json_bytes).hexdigest().
        return hashlib.sha256(json_bytes).hexdigest()


def compute_hash(obj: Any) -> str:
    """
    Computes a SHA-256 hash of a JSON-serializable object using the CanonicalHashingStrategy (RFC 8785).
    """
    return CanonicalHashingStrategy().compute_hash(obj)


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
        try:
            computed_hash = compute_hash(payload)
        except (TypeError, ValueError):
            # If payload contains non-deterministic data, verification fails
            return False

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
            if i == 0 and trusted_root_hash and stored_hash != trusted_root_hash:
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
