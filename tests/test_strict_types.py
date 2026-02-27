import pytest
from pydantic import ValidationError
from coreason_manifest.spec.core.skills import SkillDefinition
from coreason_manifest.spec.core.types import MiddlewareDef

def test_skill_definition_strict_types():
    # Valid
    SkillDefinition(description="desc", parameters={"key": "value"})

    # Invalid: description should be str, not int
    with pytest.raises(ValidationError):
        SkillDefinition(description=123, parameters={})

    # Invalid: parameters should be dict, not list
    with pytest.raises(ValidationError):
        SkillDefinition(parameters=["invalid"])

def test_middleware_def_strict_types():
    # Valid
    MiddlewareDef(ref="module.py:Class", config={"a": 1})

    # Invalid: config should be dict
    with pytest.raises(ValidationError):
        MiddlewareDef(ref="module.py:Class", config="invalid")
