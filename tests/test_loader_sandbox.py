import sys
from pathlib import Path

import pytest

from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
from coreason_manifest.utils.loader import SandboxedPathFinder, load_agent_from_ref, sandbox_context


def test_sandboxed_import_resolution(tmp_path: Path) -> None:
    jail = tmp_path / "jail_sandbox"
    jail.mkdir()

    (jail / "utils.py").write_text("def helper(): return 'helped'")
    (jail / "utils.py").chmod(0o600)
    (jail / "agent.py").write_text("import utils\nclass Agent:\n    def run(self): return utils.helper()")
    (jail / "agent.py").chmod(0o600)

    # Ensure jail is NOT in sys.path
    assert str(jail) not in sys.path

    # Load agent
    agent_cls = load_agent_from_ref("agent.py:Agent", root_dir=jail)
    agent = agent_cls()
    assert agent.run() == "helped"

    # Ensure jail is STILL not in sys.path
    assert str(jail) not in sys.path


def test_sandboxed_import_isolation(tmp_path: Path) -> None:
    jail1 = tmp_path / "jail1"
    jail1.mkdir()
    (jail1 / "config.py").write_text("VALUE = 1")
    (jail1 / "config.py").chmod(0o600)
    (jail1 / "agent.py").write_text("import config\nclass Agent:\n    val = config.VALUE")
    (jail1 / "agent.py").chmod(0o600)

    jail2 = tmp_path / "jail2"
    jail2.mkdir()
    (jail2 / "config.py").write_text("VALUE = 2")
    (jail2 / "config.py").chmod(0o600)
    (jail2 / "agent.py").write_text("import config\nclass Agent:\n    val = config.VALUE")
    (jail2 / "agent.py").chmod(0o600)

    # Load from jail1
    agent1_cls = load_agent_from_ref("agent.py:Agent", root_dir=jail1)
    # Use getattr because Mypy sees agent1_cls as 'type' which doesn't have 'val'
    assert getattr(agent1_cls, "val") == 1  # noqa: B009

    # Load from jail2
    try:
        agent2_cls = load_agent_from_ref("agent.py:Agent", root_dir=jail2)
        assert getattr(agent2_cls, "val") == 2  # noqa: B009
    except AssertionError:
        pytest.fail("Sandboxed isolation failed: Module collision in sys.modules")


def test_loader_path_traversal_in_find_spec(tmp_path: Path) -> None:
    """Ensure SandboxedPathFinder strictly prevents path traversal via symlinks."""
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    # Create a malicious symlink inside the jail that points outside
    malicious_link = jail / "malicious_module"
    try:
        malicious_link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks not supported")

    # Ensure target exists and is a package if we expect it to be found
    (outside / "__init__.py").touch()

    finder = SandboxedPathFinder()

    # Execute the finder within the sandbox context
    with sandbox_context(jail):
        with pytest.raises(SecurityJailViolationError, match="escapes the root directory"):
            # When find_spec looks for "malicious_module", it resolves to the 'outside' dir
            # find_spec calls resolve() on origin
            spec = finder.find_spec("malicious_module")
            # If it returns None, the test fails (DID NOT RAISE).
            # We need to ensure it finds it.
            # Symlink points to outside dir which has __init__.py -> valid package.
            if spec is None:
                pytest.fail("find_spec returned None instead of raising SecurityJailViolationError")
