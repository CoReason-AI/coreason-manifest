import pytest
import yaml
from pydantic import BaseModel

from coreason_manifest.utils.loader import (
    CircularReferenceError,
    ExceptionTranslator,
    ManifestSyntaxError,
    SecurityExceptionError,
)


def test_pydantic_translation() -> None:
    class Model(BaseModel):
        x: int

    with pytest.raises(ManifestSyntaxError) as excinfo, ExceptionTranslator():
        Model(x="foo")

    assert excinfo.value.json_path == "#/x"
    assert "Input should be a valid integer" in str(excinfo.value)

def test_yaml_translation() -> None:
    with pytest.raises(ManifestSyntaxError) as excinfo, ExceptionTranslator():
        yaml.safe_load("{a: [}")

    assert "YAML parsing failed" in str(excinfo.value)

def test_security_translation() -> None:
    with pytest.raises(SecurityExceptionError) as excinfo, ExceptionTranslator():
        raise CircularReferenceError(["a", "b", "a"])

    assert "Circular reference detected" in str(excinfo.value)
