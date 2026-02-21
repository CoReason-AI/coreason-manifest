from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
from coreason_manifest.utils.loader import SandboxedPathFinder, _jail_root_var, load_agent_from_ref, sandbox_context


def test_loader_symlink_loop_in_find_spec(tmp_path: Path) -> None:
    """
    Cover lines 124-125 in loader.py: Symlink loop in potential_path.resolve()
    """
    finder = SandboxedPathFinder()
    jail = tmp_path / "jail"
    jail.mkdir()

    # We mock _jail_root_var because we can't easily create a real symlink loop that pathlib catches
    # as RuntimeError in a safe way without OS support or creating real loop.
    # Actually we can mock resolve() to raise RuntimeError("Symlink loop")

    token = _jail_root_var.set(jail)
    try:
        with (
            patch("pathlib.Path.resolve", side_effect=RuntimeError("Symlink loop detected")),
            pytest.raises(SecurityJailViolationError, match="Symlink loop in foo"),
        ):
            finder.find_spec("foo")
    finally:
        _jail_root_var.reset(token)


def test_loader_runtime_error_in_find_spec(tmp_path: Path) -> None:
    """
    Cover line 127 in loader.py: Other RuntimeError (not Symlink) -> returns None
    """
    finder = SandboxedPathFinder()
    jail = tmp_path / "jail"
    jail.mkdir()

    token = _jail_root_var.set(jail)
    try:
        with patch("pathlib.Path.resolve", side_effect=RuntimeError("Other error")):
            assert finder.find_spec("foo") is None
    finally:
        _jail_root_var.reset(token)


def test_loader_agent_symlink_resolution_failure(tmp_path: Path) -> None:
    """
    Cover line 319 in loader.py: RuntimeError during file_path resolution (Symlink loop)
    """
    jail = tmp_path / "jail"
    jail.mkdir()

    # We pass a reference that triggers resolution
    # Mock (root_dir / file_ref).resolve(strict=True) to raise RuntimeError("Symlink ...")

    with (
        patch("pathlib.Path.resolve", side_effect=RuntimeError("Symlink loop")),
        pytest.raises(SecurityJailViolationError, match="Symlink resolution failed"),
    ):
        load_agent_from_ref("foo.py:Agent", root_dir=jail)


def test_loader_agent_unsafe_permissions(tmp_path: Path) -> None:
    """
    Cover line 312: SecurityJailViolationError for unsafe permissions (S_IWOTH | S_IWGRP)
    """
    import stat

    jail = tmp_path / "jail"
    jail.mkdir()
    agent_file = jail / "agent.py"
    agent_file.write_text("class Agent: pass")

    # Simulate S_IWOTH
    with patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_mode = stat.S_IWOTH
        with pytest.raises(SecurityJailViolationError, match="unsafe writable permissions"):
            load_agent_from_ref("agent.py:Agent", root_dir=jail)

    # Simulate S_IWGRP
    with patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_mode = stat.S_IWGRP
        with pytest.raises(SecurityJailViolationError, match="unsafe writable permissions"):
            load_agent_from_ref("agent.py:Agent", root_dir=jail)


def test_loader_path_traversal_in_find_spec(tmp_path: Path) -> None:
    """
    Cover line 124 in loader.py: Reference escapes root directory in find_spec
    """
    # 1. Setup isolated directories
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    # 2. Create a malicious symlink inside the jail that points outside
    malicious_link = jail / "malicious_module"
    malicious_link.symlink_to(outside, target_is_directory=True)

    finder = SandboxedPathFinder()

    # 3. Execute the finder within the sandbox context
    with (
        sandbox_context(jail),
        pytest.raises(SecurityJailViolationError, match="escapes the root directory"),
    ):
        # When find_spec looks for "malicious_module", it resolves to the 'outside' dir
        finder.find_spec("malicious_module")


def test_loader_execution_success(tmp_path: Path) -> None:
    """
    Explicitly cover the module execution block (lines 325-383) in loader.py.
    This ensures 100% coverage even if other integration tests are skipped.
    """
    jail = tmp_path / "jail"
    jail.mkdir()
    (jail / "agent.py").write_text("class Agent:\n    def run(self): return 'ok'")
    (jail / "agent.py").chmod(0o600)

    # Run
    cls = load_agent_from_ref("agent.py:Agent", root_dir=jail)
    assert cls().run() == "ok"
