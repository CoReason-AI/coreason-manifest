from typing import Any

import pytest

from coreason_manifest.core.primitives.types import DataClassification


def test_import() -> None:
    import coreason_manifest

    assert coreason_manifest is not None


@pytest.fixture
def mock_factory() -> Any:
    from coreason_manifest.toolkit.mock import MockFactory

    return MockFactory(seed=42)


def test_sota_passport_instantiation(mock_factory: Any) -> None:
    """
    Ensures the 2026+ Architectural Hardening fields are properly validated.
    Epic 6 is fully merged and models accept these kwargs.
    """
    # Test 1: Standard Multi-Dimensional Bounds
    passport = mock_factory.generate_mock_passport(classification=DataClassification.RESTRICTED)
    assert passport.delegation.max_tokens == 50_000
    assert passport.delegation.max_compute_time_ms == 120_000
    assert passport.delegation.max_data_classification == DataClassification.RESTRICTED
    assert passport.delegation.caep_stream_uri == "https://mock-ssf.local.coreason.ai/stream"
    assert passport.signature_algorithm == "ML-DSA-65"
    assert passport.parent_passport_id is None

    # Test 2: Swarm Lineage Fuzzing
    child_passport = mock_factory.generate_mock_passport(is_swarm_child=True)
    assert child_passport.parent_passport_id is not None
    assert "mock_parent_jti_" in child_passport.parent_passport_id


def test_swarm_orchestration_schema() -> None:
    from coreason_manifest.core.workflow.nodes.swarm import SwarmNode, TournamentConfig
    from pydantic import ValidationError

    # Valid Instantiation
    valid_swarm = SwarmNode(
        id="test_swarm",
        worker_profile="researcher",
        workload_variable="urls",
        output_variable="report",
        distribution_strategy="island_model",
        sub_swarm_count=3,
        isolation_turns=5,
        reducer_function="tournament",
        tournament_config=TournamentConfig(),
        max_concurrency=10,
        operational_policy=None,
    )
    assert valid_swarm.distribution_strategy == "island_model"

    # Invalid: Tournament without config
    with pytest.raises(ValidationError) as exc:
        SwarmNode(
            id="test_swarm", worker_profile="researcher", workload_variable="urls", output_variable="report",
            distribution_strategy="sharded", reducer_function="tournament",
            max_concurrency=10, operational_policy=None,
        )
    assert "requires a 'tournament_config'" in str(exc.value)

    # Invalid: Compute bound without operational policy
    with pytest.raises(ValidationError) as exc:
        SwarmNode(
            id="test_swarm", worker_profile="researcher", workload_variable="urls", output_variable="report",
            distribution_strategy="sharded", pruning_strategy="compute_bound",
            max_concurrency=10, reducer_function="concat", operational_policy=None,
        )
    assert "requires an 'operational_policy'" in str(exc.value)
