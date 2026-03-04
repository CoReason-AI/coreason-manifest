# Prosperity-3.0
import pytest
from pydantic import ValidationError

from coreason_manifest.spec.intent_protocols import (
    ConstraintConfig,
    GracefulDegradationPolicy,
    UniversalIntentURI,
)


def test_constraint_config() -> None:
    config = ConstraintConfig(
        max_latency_ms=1000,
        requires_hipaa_compliance=True,
        allowed_compute_regions=["us-east-1"],
    )
    assert config.max_latency_ms == 1000
    assert config.requires_hipaa_compliance is True
    assert config.allowed_compute_regions == ["us-east-1"]


def test_graceful_degradation_policy() -> None:
    policy = GracefulDegradationPolicy(
        droppable_constraints=["max_latency_ms"],
        fallback_timeout_ms=5000,
        allow_synthetic_bootstrapping=True,
    )
    assert policy.droppable_constraints == ["max_latency_ms"]
    assert policy.fallback_timeout_ms == 5000
    assert policy.allow_synthetic_bootstrapping is True


def test_universal_intent_uri_valid() -> None:
    config = ConstraintConfig(
        max_latency_ms=500,
        requires_hipaa_compliance=False,
        allowed_compute_regions=["eu-central-1"],
    )
    policy = GracefulDegradationPolicy(
        droppable_constraints=["max_latency_ms"],
        fallback_timeout_ms=10000,
        allow_synthetic_bootstrapping=False,
    )

    uri = UniversalIntentURI(
        scheme="ibo",
        ecosystem_target="huggingface",
        semantic_payload="Identify relevant text snippets",
        constraints=config,
        degradation_policy=policy,
    )

    assert uri.scheme == "ibo"
    assert uri.ecosystem_target == "huggingface"
    assert uri.semantic_payload == "Identify relevant text snippets"
    assert uri.constraints == config
    assert uri.degradation_policy == policy


def test_universal_intent_uri_invalid_scheme() -> None:
    config = ConstraintConfig(
        max_latency_ms=500,
        requires_hipaa_compliance=False,
        allowed_compute_regions=["eu-central-1"],
    )

    with pytest.raises(ValidationError):
        UniversalIntentURI(
            scheme="invalid_scheme",  # type: ignore
            ecosystem_target="huggingface",
            semantic_payload="Identify relevant text snippets",
            constraints=config,
            degradation_policy=None,
        )
