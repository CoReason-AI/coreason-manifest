# tests/test_integrity_canonical.py

import enum
import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import BaseModel

from coreason_manifest.utils.integrity import compute_hash, reconstruct_payload, verify_merkle_proof


class TestCanonicalHashingStrategy:
    def test_primitive_hashing(self) -> None:
        """Test primitive hashing: dicts, lists, Pydantic models."""
        # Dict
        data_dict = {"a": 1, "b": "test"}
        # Expectation: {"a":1,"b":"test"} -> hash
        expected_json = '{"a":1,"b":"test"}'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(data_dict) == expected_hash

        # List
        data_list = ["b", "a"]
        # Expectation: ["b","a"] -> hash (lists preserve order)
        expected_json = '["b","a"]'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(data_list) == expected_hash

        # Pydantic Model
        class MyModel(BaseModel):
            x: int
            y: str

        data_model = MyModel(x=10, y="hello")
        # Expectation: {"x":10,"y":"hello"} -> hash
        expected_json = '{"x":10,"y":"hello"}'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(data_model) == expected_hash

    def test_missing_leniency(self) -> None:
        """Test missing leniency: custom class raises TypeError."""

        class OpaqueData:
            pass

        obj = OpaqueData()
        with pytest.raises(TypeError, match="is not deterministically serializable"):
            compute_hash(obj)

    def test_float_constraints(self) -> None:
        """Test float constraints: inf/nan raise ValueError."""
        with pytest.raises(ValueError, match="NaN and Infinity are not allowed"):
            compute_hash(float("inf"))

        with pytest.raises(ValueError, match="NaN and Infinity are not allowed"):
            compute_hash(float("nan"))

        # Finite float should work
        assert isinstance(compute_hash(1.5), str)

    def test_none_exclusion(self) -> None:
        """Test None exclusion: keys with None values are stripped."""
        data_with_none = {"a": 1, "b": None}
        data_without_none = {"a": 1}

        hash_with_none = compute_hash(data_with_none)
        hash_without_none = compute_hash(data_without_none)

        assert hash_with_none == hash_without_none

    def test_set_sorting(self) -> None:
        """Test that sets are sorted by string representation."""
        s = {"b", "a", "c"}
        # Expected: ["a","b","c"]
        expected_json = '["a","b","c"]'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(s) == expected_hash

        s2 = {1, 2, 3}
        # Expected: [1,2,3]
        expected_json = "[1,2,3]"
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(s2) == expected_hash

    def test_uuid_handling(self) -> None:
        """Test UUID conversion to string."""
        u = uuid.uuid4()
        expected_json = f'"{u!s}"'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(u) == expected_hash

    def test_datetime_handling(self) -> None:
        """Test datetime conversion to UTC ISO-8601 with microseconds."""
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        expected_str = "2023-01-01T12:00:00.000000Z"
        expected_json = f'"{expected_str}"'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(dt) == expected_hash

        # Naive datetime should be treated as UTC
        dt_naive = datetime(2023, 1, 1, 12, 0, 0)
        assert compute_hash(dt_naive) == expected_hash

    def test_protected_keys(self) -> None:
        """Test stripping of protected keys."""
        data = {
            "a": 1,
            "execution_hash": "remove me",
            "signature": "remove me",
            "__internal": "remove me",
        }
        expected_data = {"a": 1}
        assert compute_hash(data) == compute_hash(expected_data)

    def test_verify_merkle_with_nondeterministic_payload(self) -> None:
        """Test verify_merkle_proof handles non-deterministic payloads gracefully."""

        class OpaqueData:
            pass

        # Create a trace with a node containing an opaque object
        # reconstruct_payload will accept the dict, but compute_hash will fail
        node = {
            "data": OpaqueData(),
            "execution_hash": "some_hash",
            "parent_hashes": [],
        }
        trace = [node]

        # Should return False (invalid), catching the TypeError internally
        assert verify_merkle_proof(trace) is False

    def test_enum_hashing(self) -> None:
        """Test that an Enum member hashes successfully based on its value."""

        class Color(enum.Enum):
            RED = "red"
            BLUE = "blue"

        # Enum value is string
        assert compute_hash(Color.RED) == compute_hash("red")
        assert compute_hash(Color.BLUE) == compute_hash("blue")

    def test_mixed_type_dict_keys(self) -> None:
        """Assert that {1: "a", "2": "b"} does not raise a TypeError and hashes consistently."""
        data: dict[int | str, str] = {1: "a", "2": "b"}
        # Keys sorted by str(key): "1", "2"
        # 1 -> "1", "2" -> "2"
        # Expected JSON: {"1":"a","2":"b"}
        expected_json = '{"1":"a","2":"b"}'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()

        assert compute_hash(data) == expected_hash

        # Order independence
        data2: dict[int | str, str] = {"2": "b", 1: "a"}
        assert compute_hash(data2) == expected_hash

    def test_set_mixed_types(self) -> None:
        """Assert that set([1, "1"]) hashes deterministically without colliding or dropping data."""
        s = {1, "1"}
        # Sorted by f"{type(x).__name__}:{x}"
        # 1 -> "int:1"
        # "1" -> "str:1"
        # "int:1" comes before "str:1" alphabetically
        # Expected list: [1, "1"]

        # SOTA Update: Sorted by JSON dump.
        # json(1) -> "1"
        # json("1") -> "\"1\""
        # "\"1\"" < "1" because ascii '"' (34) < '1' (49). So "1" comes first.

        expected_json = '["1",1]'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()

        assert compute_hash(s) == expected_hash

    def test_float_integer_truncation(self) -> None:
        """Assert that 1.0 and 1 yield the exact same SHA-256 hash."""
        assert compute_hash(1.0) == compute_hash(1)
        assert compute_hash(1.5) != compute_hash(1)

    def test_tuple_hashing(self) -> None:
        """Test tuple hashing coverage."""
        t = ("a", 1)
        # Treated as list
        assert compute_hash(t) == compute_hash(["a", 1])

    def test_verify_merkle_cycle(self) -> None:
        """Test cycle detection in verify_merkle_proof."""
        # A -> B -> A
        node_a = {"id": "a", "parent_hashes": ["hash_b"]}
        node_b = {"id": "b", "parent_hashes": ["hash_a"]}

        node_a["execution_hash"] = "hash_a"
        node_b["execution_hash"] = "hash_b"

        trace = [node_a, node_b]
        assert verify_merkle_proof(trace) is False

    def test_verify_merkle_genesis_mismatch(self) -> None:
        """Test genesis node hash mismatch."""
        node: dict[str, Any] = {"x": 1}
        payload = reconstruct_payload(node)
        h = compute_hash(payload)
        node["execution_hash"] = h

        # Pass a trusted root that doesn't match
        assert verify_merkle_proof([node], trusted_root_hash="wrong_hash") is False

        # Pass correct trusted root
        assert verify_merkle_proof([node], trusted_root_hash=h) is True

    def test_nested_signature_retention(self) -> None:
        """Assert that 'signature' is only stripped from the root, not nested dicts."""
        data = {"signature": "root_signature_to_strip", "payload": {"signature": "keep_me"}}
        # Expected behavior: root signature goes away, payload signature stays.
        hashed = compute_hash(data)
        expected_json = '{"payload":{"signature":"keep_me"}}'
        assert hashed == hashlib.sha256(expected_json.encode("utf-8")).hexdigest()

    def test_key_stringification_collision(self) -> None:
        """Assert that mixing types that stringify identically raises a ValueError to prevent silent data loss."""
        data: dict[Any, Any] = {1: "a", "1": "b"}
        with pytest.raises(ValueError, match="Collision detected"):
            compute_hash(data)

    def test_complex_set_determinism(self) -> None:
        """Assert that sets containing nested unordered elements hash perfectly deterministically."""
        s1 = frozenset({frozenset({2, 1}), frozenset({4, 3})})
        s2 = frozenset({frozenset({3, 4}), frozenset({1, 2})})
        # Despite different insertion/memory orders, the canonical JSON array representations must sort identically.
        assert compute_hash(s1) == compute_hash(s2)

    def test_nested_compute_hash(self) -> None:
        """Test that nested objects with compute_hash are handled correctly."""

        class NestedHasher:
            def compute_hash(self) -> str:
                return "nested_hash"

        data = {"key": NestedHasher()}
        h = compute_hash(data)
        # Expected: {"key":"nested_hash"}
        expected_json = '{"key":"nested_hash"}'
        assert h == hashlib.sha256(expected_json.encode("utf-8")).hexdigest()

    def test_nested_float_constraints(self) -> None:
        """Test that NaN/Inf checks are hit for nested values."""
        with pytest.raises(ValueError, match="NaN and Infinity"):
            compute_hash({"key": float("inf")})

        with pytest.raises(ValueError, match="NaN and Infinity"):
            compute_hash([float("nan")])
