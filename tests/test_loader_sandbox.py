import sys
from pathlib import Path
import pytest
from coreason_manifest.utils.loader import load_agent_from_ref

def test_sandboxed_import_resolution(tmp_path: Path) -> None:
    jail = tmp_path / "jail_sandbox"
    jail.mkdir()

    (jail / "utils.py").write_text("def helper(): return 'helped'")
    (jail / "agent.py").write_text("import utils\nclass Agent:\n    def run(self): return utils.helper()")

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
    (jail1 / "agent.py").write_text("import config\nclass Agent:\n    val = config.VALUE")

    jail2 = tmp_path / "jail2"
    jail2.mkdir()
    (jail2 / "config.py").write_text("VALUE = 2")
    (jail2 / "agent.py").write_text("import config\nclass Agent:\n    val = config.VALUE")

    # Load from jail1
    agent1_cls = load_agent_from_ref("agent.py:Agent", root_dir=jail1)
    assert agent1_cls.val == 1

    # Load from jail2
    # Note: If 'config' is in sys.modules, jail2 might reuse it if we are not careful about cleaning sys.modules
    # My implementation puts 'config' in sys.modules.
    # So if I load jail1/agent.py, it loads jail1/config.py as 'config' in sys.modules.
    # Then loading jail2/agent.py imports 'config'. usage standard import. It finds 'config' in sys.modules.
    # It uses jail1's config!
    # SOTA "Secure Contextual Sandboxing" requires isolation.
    # My implementation FAILED to provide isolation if module names collide.
    # I noted this in my thought process.

    # If this test fails, I need to fix it by removing modules from sys.modules after load?
    # But if I remove it, the agent class might break if it relies on the module object being consistent.
    # However, for the purpose of "loading", maybe we can force reload?

    # Let's see if it fails.
    try:
        agent2_cls = load_agent_from_ref("agent.py:Agent", root_dir=jail2)
        assert agent2_cls.val == 2
    except AssertionError:
        pytest.fail("Sandboxed isolation failed: Module collision in sys.modules")
