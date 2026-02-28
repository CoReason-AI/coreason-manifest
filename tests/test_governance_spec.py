import pytest
from pydantic import ValidationError

from coreason_manifest.core.oversight.governance import (
    OperationalPolicy,
    RequestCriticality,
    SemanticCacheConfig,
    TrafficPolicy,
)


def test_request_criticality() -> None:
    assert RequestCriticality.CRITICAL.value == 10  # noqa: S101
    assert RequestCriticality.STANDARD.value == 5  # noqa: S101
    assert RequestCriticality.SHEDDABLE.value == 1  # noqa: S101


def test_semantic_cache_config() -> None:
    # Valid
    config = SemanticCacheConfig(enabled=True, similarity_threshold=0.9, ttl_seconds=1800)
    assert config.enabled is True  # noqa: S101
    assert config.similarity_threshold == 0.9  # noqa: S101
    assert config.ttl_seconds == 1800  # noqa: S101

    # Default
    config_default = SemanticCacheConfig()
    assert config_default.enabled  # noqa: S101
    assert config_default.similarity_threshold == 0.85  # noqa: S101
    assert config_default.ttl_seconds == 3600  # noqa: S101

    # Invalid threshold
    with pytest.raises(ValidationError):
        SemanticCacheConfig(similarity_threshold=-0.1)

    with pytest.raises(ValidationError):
        SemanticCacheConfig(similarity_threshold=1.1)


def test_traffic_policy() -> None:
    # Valid
    policy = TrafficPolicy(
        criticality=RequestCriticality.CRITICAL,
        rate_limit_rpm=100,
        rate_limit_tpm=10000,
        semantic_cache=SemanticCacheConfig(),
    )
    assert policy.criticality == RequestCriticality.CRITICAL  # noqa: S101
    assert policy.rate_limit_rpm == 100  # noqa: S101
    assert policy.rate_limit_tpm == 10000  # noqa: S101
    assert policy.semantic_cache is not None  # noqa: S101

    # Invalid limits (should be gt 0)
    with pytest.raises(ValidationError):
        TrafficPolicy(rate_limit_rpm=0)

    with pytest.raises(ValidationError):
        TrafficPolicy(rate_limit_rpm=-10)

    with pytest.raises(ValidationError):
        TrafficPolicy(rate_limit_tpm=0)


def test_operational_policy_traffic() -> None:
    policy = OperationalPolicy(traffic=TrafficPolicy())
    assert policy.traffic is not None  # noqa: S101
    assert policy.traffic.criticality == RequestCriticality.STANDARD  # noqa: S101
