from typing import Any

import pytest

from coreason_manifest.spec.ontology import BaseNodeProfile


def test_base_node_profile_domain_extensions_valid() -> None:
    node = BaseNodeProfile(
        description="test node",
        domain_extensions={"a": "b", "c": {"d": 1}},
    )
    assert node.domain_extensions == {"a": "b", "c": {"d": 1}}


def test_base_node_profile_domain_extensions_none() -> None:
    node = BaseNodeProfile(
        description="test node",
        domain_extensions=None,
    )
    assert node.domain_extensions is None


def test_base_node_profile_domain_extensions_depth_exceeded() -> None:
    deep_dict: Any = "leaf"
    for _ in range(6):
        deep_dict = {"key": deep_dict}

    with pytest.raises(ValueError, match="domain_extensions exceeds maximum allowed depth of 5"):
        BaseNodeProfile(
            description="test node",
            domain_extensions=deep_dict,
        )


def test_base_node_profile_domain_extensions_invalid_keys() -> None:
    with pytest.raises(ValueError, match="domain_extensions keys must be strings"):
        BaseNodeProfile(
            description="test node",
            domain_extensions={1: "a"},  # type: ignore
        )


def test_base_node_profile_domain_extensions_key_too_long() -> None:
    with pytest.raises(ValueError, match="domain_extensions key exceeds maximum length of 255 characters"):
        BaseNodeProfile(
            description="test node",
            domain_extensions={"a" * 256: "b"},
        )


def test_base_node_profile_domain_extensions_invalid_leaf() -> None:
    class CustomObj:
        pass

    with pytest.raises(ValueError, match="domain_extensions leaf values must be JSON primitives, got CustomObj"):
        BaseNodeProfile(
            description="test node",
            domain_extensions={"a": CustomObj()},
        )


def test_base_node_profile_domain_extensions_not_dict() -> None:
    with pytest.raises(ValueError, match="domain_extensions must be a dictionary"):
        BaseNodeProfile(
            description="test node",
            domain_extensions=["not a dict"],  # type: ignore
        )


def test_base_node_profile_domain_extensions_list_depth_exceeded() -> None:
    deep_list: Any = "leaf"
    for _ in range(6):
        deep_list = [deep_list]

    with pytest.raises(ValueError, match="domain_extensions exceeds maximum allowed depth of 5"):
        BaseNodeProfile(
            description="test node",
            domain_extensions={"a": deep_list},
        )
