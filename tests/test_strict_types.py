import pytest
from pydantic import ValidationError
from coreason_manifest.spec.core.contracts import AtomicSkill
from coreason_manifest.spec.core.types import MiddlewareDef, StrictPayload
from collections.abc import Mapping

def test_atomic_skill_strict_types():
    # Valid
    AtomicSkill(name="skill", version="1.0.0", capabilities=["caps"], inputs_schema={"a": "b"})

    # Invalid: capabilities should be list, not int
    with pytest.raises(ValidationError):
        AtomicSkill(capabilities=123)

    # Invalid: inputs_schema should be dict, not list
    with pytest.raises(ValidationError):
        AtomicSkill(inputs_schema=["invalid"])

def test_middleware_def_strict_types():
    # Valid
    MiddlewareDef(ref="module.py:Class", config={"a": 1})

    # Invalid: config should be dict
    with pytest.raises(ValidationError):
        MiddlewareDef(ref="module.py:Class", config="invalid")

def test_strict_payload_immutability():
    payload = StrictPayload(data={"a": [1, 2]})

    # Check type
    if isinstance(payload.data, dict):
        pytest.fail(f"payload.data is mutable dict: {type(payload.data)}")

    assert isinstance(payload.data, Mapping)

    # Check top level immutability
    with pytest.raises(TypeError):
        payload.data["a"] = [3]

    # Check nested list immutability (converted to tuple)
    val = payload.data["a"]
    assert isinstance(val, tuple)
