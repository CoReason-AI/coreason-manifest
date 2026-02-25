# src/coreason_manifest/utils/integrity.py

import enum
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
    Converts a datetime to a strict UTC string format: YYYY-MM-DDTHH:MM:SS.mmmmmmZ
    """
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=UTC)

    # Convert to UTC
    dt_utc = dt.astimezone(UTC)

    # Format with microsecond precision to prevent sub-second trace collisions.
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


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
        # Nested Hashing:
        if hasattr(obj, "compute_hash"):
            return str(obj.compute_hash())

        # Enums:
        if isinstance(obj, enum.Enum):
            return self._recursive_sort_and_sanitize(obj.value)

        # Dictionaries:
        if isinstance(obj, dict):
            sanitized_dict = {}
            seen_keys = set()

            # Sort by stringified key to prevent mixed-type TypeError
            for k, v in sorted(obj.items(), key=lambda item: str(item[0])):
                if v is None or str(k).startswith("__"):
                    continue

                str_k = str(k)
                if str_k in seen_keys:
                    raise ValueError(f"Canonical JSON dictionary keys must be uniquely stringifiable. Collision detected for key: '{str_k}'")

                seen_keys.add(str_k)
                sanitized_dict[str_k] = self._recursive_sort_and_sanitize(v)
            return sanitized_dict

        # Iterables (List/Tuple):
        if isinstance(obj, (list, tuple)):
            # Recursively process items.
            return [self._recursive_sort_and_sanitize(x) for x in obj]

        # Sets:
        if isinstance(obj, (set, frozenset)):
            # 1. Sanitize all items first
            sanitized_items = [self._recursive_sort_and_sanitize(x) for x in obj]
            # 2. Sort by their deterministic JSON string representation
            sanitized_items.sort(
                key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            )
            return sanitized_items

        if isinstance(obj, uuid.UUID):
            # Convert to string via str(obj).
            return str(obj)

        if isinstance(obj, datetime):
            # Enforce conversion to UTC and format as a strict ISO-8601 string.
            return to_canonical_timestamp(obj)

        if isinstance(obj, BaseModel):
            # Use model_dump(exclude_none=True, mode="python") and recursively process.
            excludes = getattr(obj, "_hash_exclude_", None)
            return self._recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, exclude=excludes, mode="python"))

        if hasattr(obj, "model_dump"):
            # Pydantic v2 or compatible
            return self._recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, mode="python"))

        # Floats (The RFC 8785 Integer Fix):
        if isinstance(obj, float):
            # Allow finite floats. Explicitly raise a ValueError if math.isnan(obj) or math.isinf(obj).
            if math.isnan(obj) or math.isinf(obj):
                raise ValueError("NaN and Infinity are not allowed in Canonical JSON")
            # RFC 8785: whole numbers must not have fractional parts
            if obj.is_integer():
                return int(obj)
            return obj

        # Primitives (int, str, bool) & None: Return as-is.
        if isinstance(obj, (int, str, bool)) or obj is None:
            return obj

        # Strict Rejection (The Core Mandate)
        raise TypeError(f"Object of type {type(obj)} is not deterministically serializable.")

    def compute_hash(self, obj: Any) -> str:
        if hasattr(obj, "compute_hash"):
            # Self-hashing objects (avoid infinite recursion if they call back here)
            return str(obj.compute_hash())

        # Strip root-level cryptographic keys to avoid hashing the hash
        if isinstance(obj, dict):
            obj = obj.copy()
            obj.pop("execution_hash", None)
            obj.pop("signature", None)
        elif isinstance(obj, BaseModel):
            # Pydantic models need to be dumped to be mutable dicts for popping keys,
            # OR we rely on _recursive_sort_and_sanitize handling Pydantic.
            # But we need to strip keys BEFORE recursion to avoid recursive stripping.
            # So we dump it here.
            excludes = getattr(obj, "_hash_exclude_", None)
            obj = obj.model_dump(exclude_none=True, exclude=excludes, mode="python")
            obj.pop("execution_hash", None)
            obj.pop("signature", None)
        elif hasattr(obj, "model_dump"):
             obj = obj.model_dump(mode="python")
             obj.pop("execution_hash", None)
             obj.pop("signature", None)

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

    for payload in sorted_trace:
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
            # Genesis Node (can be multiple in disconnected DAGs)
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
