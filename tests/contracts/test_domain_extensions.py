from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings

from coreason_manifest.spec.ontology import BaseNodeProfile

# 1. Define the Valid Mathematical Space for domain_extensions
scalar_st = (
    st.none() | st.booleans() | st.floats(allow_nan=False, allow_infinity=False) | st.integers() | st.text(max_size=100)
)

valid_extensions_st = st.dictionaries(
    keys=st.text(min_size=1, max_size=255),
    values=st.recursive(
        scalar_st,
        lambda children: (
            st.lists(children, max_size=5) | st.dictionaries(st.text(min_size=1, max_size=255), children, max_size=5)
        ),
        max_leaves=10,
    ),
    max_size=10,
)


@given(extensions=st.one_of(st.none(), valid_extensions_st))
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_base_node_profile_domain_extensions_fuzz_valid_space(extensions: Any) -> None:
    """
    AGENT INSTRUCTION: Fuzz the valid structural space using hypothesis.
    Mathematically prove that any domain_extensions payload falling UNDER
    the topological tripwires (depth <= 5, key length <= 255) is strictly accepted.
    """
    node = BaseNodeProfile(
        description="fuzzed node",
        domain_extensions=extensions,
    )
    assert node.domain_extensions == extensions


# --- RETAIN ALL ATOMIC BOUNDARY TESTS BELOW THIS LINE ---


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
