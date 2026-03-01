import pytest
from pydantic import ValidationError

from coreason_manifest.core.state.ephemeral import (
    LocalStateManifest,
    LocalVariable,
    LocalVariableType,
)


def test_local_variable_string() -> None:
    var = LocalVariable(type=LocalVariableType.STRING, default="hello", description="A string var")
    assert var.type == LocalVariableType.STRING
    assert var.default == "hello"
    assert var.description == "A string var"

    with pytest.raises(ValidationError):
        LocalVariable(type=LocalVariableType.STRING, default=123)


def test_local_variable_number() -> None:
    var = LocalVariable(type=LocalVariableType.NUMBER, default=42)
    assert var.default == 42

    var_float = LocalVariable(type=LocalVariableType.NUMBER, default=3.14)
    assert var_float.default == 3.14

    with pytest.raises(ValidationError):
        LocalVariable(type=LocalVariableType.NUMBER, default="42")

    with pytest.raises(ValidationError):
        LocalVariable(type=LocalVariableType.NUMBER, default=True)


def test_local_variable_boolean() -> None:
    var = LocalVariable(type=LocalVariableType.BOOLEAN, default=True)
    assert var.default is True

    with pytest.raises(ValidationError):
        LocalVariable(type=LocalVariableType.BOOLEAN, default=1)

    with pytest.raises(ValidationError):
        LocalVariable(type=LocalVariableType.BOOLEAN, default="True")


def test_local_variable_list() -> None:
    var = LocalVariable(type=LocalVariableType.LIST, default=[1, 2, 3])
    assert var.default == [1, 2, 3]

    with pytest.raises(ValidationError):
        LocalVariable(type=LocalVariableType.LIST, default="[1, 2, 3]")


def test_local_variable_dict() -> None:
    var = LocalVariable(type=LocalVariableType.DICT, default={"a": 1})
    assert var.default == {"a": 1}

    with pytest.raises(ValidationError):
        LocalVariable(type=LocalVariableType.DICT, default=["a", 1])


def test_local_variable_no_default() -> None:
    var = LocalVariable(type=LocalVariableType.STRING)
    assert var.default is None


def test_local_state_manifest() -> None:
    manifest = LocalStateManifest(
        keys={
            "search_query": LocalVariable(type=LocalVariableType.STRING, default=""),
            "is_open": LocalVariable(type=LocalVariableType.BOOLEAN, default=False),
        }
    )
    assert len(manifest.keys) == 2
    assert "search_query" in manifest.keys
    assert manifest.keys["search_query"].type == LocalVariableType.STRING
    assert manifest.keys["is_open"].default is False


def test_local_state_manifest_default() -> None:
    manifest = LocalStateManifest()
    assert manifest.keys == {}
