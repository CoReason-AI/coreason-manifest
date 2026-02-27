import pytest
from coreason_manifest.utils.integrity import CanonicalHashingStrategy, compute_hash

def test_canonical_hashing_none():
    # Should preserve None
    data = {"a": None}
    s = CanonicalHashingStrategy()
    res = s._recursive_sort_and_sanitize(data)
    assert res == data

    # Check output
    h = compute_hash(data)
    assert h # Should not fail

def test_canonical_hashing_dunder():
    # Should preserve dunder
    data = {"__class__": "foo"}
    s = CanonicalHashingStrategy()
    res = s._recursive_sort_and_sanitize(data)
    assert "__class__" in res

def test_canonical_hashing_mode_json():
    # Enums etc should work via model_dump(mode='json')
    from enum import Enum
    from pydantic import BaseModel

    class E(str, Enum):
        A = "a"

    class M(BaseModel):
        e: E

    m = M(e=E.A)
    # mode='json' converts Enum to value
    h = compute_hash(m)
    assert h
