# tests/test_integrity_canonical.py

import json
import hashlib
import pytest
import math
import uuid
from datetime import datetime, UTC
from pydantic import BaseModel
from typing import Optional
from coreason_manifest.utils.integrity import CanonicalHashingStrategy, compute_hash

class TestCanonicalHashingStrategy:

    def test_primitive_hashing(self):
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

    def test_missing_leniency(self):
        """Test missing leniency: custom class raises TypeError."""
        class OpaqueData:
            pass

        obj = OpaqueData()
        with pytest.raises(TypeError, match="is not deterministically serializable"):
            compute_hash(obj)

    def test_float_constraints(self):
        """Test float constraints: inf/nan raise ValueError."""
        with pytest.raises(ValueError, match="NaN and Infinity are not allowed"):
            compute_hash(float('inf'))

        with pytest.raises(ValueError, match="NaN and Infinity are not allowed"):
            compute_hash(float('nan'))

        # Finite float should work
        assert isinstance(compute_hash(1.5), str)

    def test_none_exclusion(self):
        """Test None exclusion: keys with None values are stripped."""
        data_with_none = {"a": 1, "b": None}
        data_without_none = {"a": 1}

        hash_with_none = compute_hash(data_with_none)
        hash_without_none = compute_hash(data_without_none)

        assert hash_with_none == hash_without_none

    def test_set_sorting(self):
        """Test that sets are sorted by string representation."""
        s = {"b", "a", "c"}
        # Expected: ["a","b","c"]
        expected_json = '["a","b","c"]'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(s) == expected_hash

        s2 = {1, 2, 3}
        # Expected: [1,2,3]
        expected_json = '[1,2,3]'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(s2) == expected_hash

    def test_uuid_handling(self):
        """Test UUID conversion to string."""
        u = uuid.uuid4()
        expected_json = f'"{str(u)}"'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(u) == expected_hash

    def test_datetime_handling(self):
        """Test datetime conversion to UTC ISO-8601."""
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        expected_str = "2023-01-01T12:00:00Z"
        expected_json = f'"{expected_str}"'
        expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        assert compute_hash(dt) == expected_hash

        # Naive datetime should be treated as UTC
        dt_naive = datetime(2023, 1, 1, 12, 0, 0)
        assert compute_hash(dt_naive) == expected_hash

    def test_protected_keys(self):
        """Test stripping of protected keys."""
        data = {
            "a": 1,
            "execution_hash": "remove me",
            "signature": "remove me",
            "__internal": "remove me"
        }
        expected_data = {"a": 1}
        assert compute_hash(data) == compute_hash(expected_data)
