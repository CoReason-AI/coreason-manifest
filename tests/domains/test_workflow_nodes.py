from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.workflow.nodes import SystemNode


def test_domain_extensions_rejects_deep_nesting() -> None:
    # Create depth 6 payload
    nested_payload: dict[str, Any] = {}
    current = nested_payload
    for _ in range(6):
        current["child"] = {}
        current = current["child"]

    with pytest.raises(ValidationError, match="exceeds maximum allowed depth of 5"):
        SystemNode(description="Test", domain_extensions=nested_payload)


def test_domain_extensions_rejects_long_keys() -> None:
    toxic_key = "a" * 256
    with pytest.raises(ValidationError, match="exceeds maximum length of 255 characters"):
        SystemNode(description="Test", domain_extensions={toxic_key: "value"})


def test_domain_extensions_rejects_non_json_primitives() -> None:
    class ToxicObject:
        pass

    with pytest.raises(ValidationError, match="leaf values must be JSON primitives"):
        SystemNode(description="Test", domain_extensions={"key": ToxicObject()})


def test_domain_extensions_rejects_non_string_keys() -> None:
    with pytest.raises(ValidationError, match="keys must be strings"):
        SystemNode(description="Test", domain_extensions={123: "value"})  # type: ignore


def test_domain_extensions_rejects_non_dict() -> None:
    with pytest.raises(ValidationError, match="must be a dictionary"):
        SystemNode(description="Test", domain_extensions="not a dict")  # type: ignore


def test_domain_extensions_list_recursion() -> None:
    # Adding a list with a non-json primitive to exercise list traversal code path
    class ToxicObject:
        pass

    with pytest.raises(ValidationError, match="leaf values must be JSON primitives"):
        SystemNode(description="Test", domain_extensions={"list": [1, 2, ToxicObject()]})
