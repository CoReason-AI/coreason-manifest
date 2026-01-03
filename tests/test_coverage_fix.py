# Prosperity-3.0
from pathlib import Path

import pytest

from coreason_manifest.engine import ManifestConfig, ManifestEngine
from coreason_manifest.policy import PolicyEnforcer


def test_policy_enforcer_init_missing_data_file() -> None:
    """Test that PolicyEnforcer raises FileNotFoundError if data file missing."""
    with pytest.raises(FileNotFoundError):
        PolicyEnforcer(
            policy_path=Path("src/coreason_manifest/policies/compliance.rego"),
            data_paths=["non_existent.json"],
        )


def test_manifest_config_data_paths(tmp_path: Path) -> None:
    """Test that ManifestEngine correctly assembles data paths from config."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()
    tbom_path = tmp_path / "tbom.json"
    tbom_path.touch()
    extra_path = tmp_path / "extra.json"
    extra_path.touch()

    config = ManifestConfig(
        policy_path=policy_path,
        tbom_path=tbom_path,
        extra_data_paths=[extra_path],
    )

    engine = ManifestEngine(config)

    # Check if paths were passed to enforcer
    # We check if lists have same elements
    assert len(engine.policy_enforcer.data_paths) == 2
    assert tbom_path in engine.policy_enforcer.data_paths
    assert extra_path in engine.policy_enforcer.data_paths
