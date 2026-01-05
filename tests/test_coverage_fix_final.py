# Prosperity-3.0
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.errors import IntegrityCompromisedError
from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.policy import PolicyEnforcer


def test_policy_opa_path_not_found(tmp_path: Path) -> None:
    """Test PolicyEnforcer init when opa_path is a specific path that doesn't exist."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    # Use a path with separator to trigger the else block
    invalid_opa_path = "./non_existent_opa_binary"

    with pytest.raises(FileNotFoundError) as excinfo:
        PolicyEnforcer(policy_path, opa_path=invalid_opa_path)
    assert "OPA executable not found at" in str(excinfo.value)


def test_policy_opa_deleted_race_condition(tmp_path: Path) -> None:
    """
    Test handling when OPA executable disappears between init and evaluate.
    """
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    # Use a dummy existing file as OPA
    fake_opa = tmp_path / "fake_opa"
    fake_opa.touch()

    # Make it executable (best effort)
    fake_opa.chmod(0o755)

    enforcer = PolicyEnforcer(policy_path, opa_path=str(fake_opa))

    # Simulate FileNotFoundError during execution (as if deleted)
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError) as excinfo:
            enforcer.evaluate({})
        assert "OPA executable not found at" in str(excinfo.value)


def test_integrity_symlink_directory_recursion(tmp_path: Path) -> None:
    """
    Test that a symlinked directory inside the source tree is detected and rejected.
    This specifically targets the check inside the directory iteration loop.
    """
    src = tmp_path / "src"
    src.mkdir()

    # Normal dir
    subdir = src / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("ok")

    # External target for symlink
    target = tmp_path / "target"
    target.mkdir()
    (target / "bad.txt").write_text("bad")

    # Create symlink inside subdir
    link_path = subdir / "link_to_target"
    try:
        os.symlink(target, link_path)
    except OSError:
        pytest.skip("Symlinks not supported on this platform")

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.calculate_hash(src)
    assert "Symbolic links are forbidden" in str(excinfo.value)
