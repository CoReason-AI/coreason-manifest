import pytest
from pydantic import ValidationError
from coreason_manifest.spec.core.contracts import AtomicSkill
from coreason_manifest.spec.core.types import MiddlewareDef

def test_atomic_skill_strict_types():
    # Valid
    AtomicSkill(capabilities=["caps"], inputs_schema={"a": "b"})

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
