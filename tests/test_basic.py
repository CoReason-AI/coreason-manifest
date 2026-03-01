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


def test_tournament_config() -> None:
    from coreason_manifest.core.workflow.nodes.swarm import TournamentConfig

    config = TournamentConfig()
    assert config.bracket_style == "single_elimination"
    assert config.retain_falsified_data is True
