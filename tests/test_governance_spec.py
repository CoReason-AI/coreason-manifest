import pytest
from pydantic import ValidationError

from coreason_manifest.core.oversight.governance import (
    OperationalPolicy,
    RequestCriticality,
    SemanticCacheConfig,
    TrafficPolicy,
)


def test_request_criticality() -> None:
    assert RequestCriticality.CRITICAL.value == 10
    assert RequestCriticality.STANDARD.value == 5
    assert RequestCriticality.SHEDDABLE.value == 1


def test_semantic_cache_config() -> None:
    # Valid
    config = SemanticCacheConfig(enabled=True, similarity_threshold=0.9, ttl_seconds=1800)
    assert config.enabled is True
    assert config.similarity_threshold == 0.9
    assert config.ttl_seconds == 1800

    # Default
    config_default = SemanticCacheConfig()
    assert config_default.enabled
    assert config_default.similarity_threshold == 0.85
    assert config_default.ttl_seconds == 3600

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
    assert policy.criticality == RequestCriticality.CRITICAL
    assert policy.rate_limit_rpm == 100
    assert policy.rate_limit_tpm == 10000
    assert policy.semantic_cache is not None

    # Invalid limits (should be gt 0)
    with pytest.raises(ValidationError):
        TrafficPolicy(rate_limit_rpm=0)

    with pytest.raises(ValidationError):
        TrafficPolicy(rate_limit_rpm=-10)

    with pytest.raises(ValidationError):
        TrafficPolicy(rate_limit_tpm=0)


def test_operational_policy_traffic() -> None:
    policy = OperationalPolicy(traffic=TrafficPolicy())
    assert policy.traffic is not None
    assert policy.traffic.criticality == RequestCriticality.STANDARD
