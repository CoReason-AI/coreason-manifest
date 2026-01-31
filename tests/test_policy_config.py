import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import PolicyConfig


def test_policy_config_valid() -> None:
    """Test creating a valid PolicyConfig."""
    policy = PolicyConfig(
        budget_caps={"total_cost": 50.0, "total_tokens": 10000},
        human_in_the_loop=["node1", "node2"],
        allowed_domains=["api.example.com", "google.com"],
    )
    assert policy.budget_caps["total_cost"] == 50.0
    assert "node1" in policy.human_in_the_loop
    assert "google.com" in policy.allowed_domains


def test_policy_config_defaults() -> None:
    """Test defaults for PolicyConfig."""
    policy = PolicyConfig()
    assert policy.budget_caps == {}
    assert policy.human_in_the_loop == []
    assert policy.allowed_domains == []


def test_policy_config_immutability() -> None:
    """Test that PolicyConfig is frozen."""
    policy = PolicyConfig(budget_caps={"cost": 10.0})
    with pytest.raises(ValidationError):
        policy.human_in_the_loop = ["node1"]  # type: ignore
