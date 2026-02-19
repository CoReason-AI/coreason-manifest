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
    # Use getattr because Mypy sees agent1_cls as 'type' which doesn't have 'val'
    assert getattr(agent1_cls, "val") == 1

    # Load from jail2
    try:
        agent2_cls = load_agent_from_ref("agent.py:Agent", root_dir=jail2)
        assert getattr(agent2_cls, "val") == 2
    except AssertionError:
        pytest.fail("Sandboxed isolation failed: Module collision in sys.modules")
