import pytest
from pydantic import ValidationError, BaseModel
from coreason_manifest.utils.loader import ExceptionTranslator, ManifestSyntaxError, SecurityException, CircularReferenceError
import yaml

def test_pydantic_translation():
    class Model(BaseModel):
        x: int

    with pytest.raises(ManifestSyntaxError) as excinfo:
        with ExceptionTranslator():
            Model(x="foo")

    assert excinfo.value.json_path == "#/x"
    assert "Input should be a valid integer" in str(excinfo.value)

def test_yaml_translation():
    with pytest.raises(ManifestSyntaxError) as excinfo:
        with ExceptionTranslator():
            yaml.safe_load("{a: [}")

    assert "YAML parsing failed" in str(excinfo.value)

def test_security_translation():
    with pytest.raises(SecurityException) as excinfo:
        with ExceptionTranslator():
            raise CircularReferenceError(["a", "b", "a"])

    assert "Circular reference detected" in str(excinfo.value)
