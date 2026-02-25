from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
from coreason_manifest.utils.loader import (
    SandboxedPathFinder,
    _resolve_includes,
    load_agent_from_ref,
    load_flow_from_file,
    sandbox_context,
)


# 1. find_spec returns None for nonexistent
def test_loader_nonexistent_module(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    finder = SandboxedPathFinder()
    with sandbox_context(jail):
        assert finder.find_spec("nonexistent") is None


# 2. find_spec catches generic Exception
def test_loader_exception_in_find_spec(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    finder = SandboxedPathFinder()
    with sandbox_context(jail), patch("pathlib.Path.resolve", side_effect=Exception("Generic error")):
        assert finder.find_spec("foo") is None


# 3. _resolve_refs catches loading error
def test_resolve_refs_error(tmp_path: Path) -> None:
    jail = tmp_path
    loader = MagicMock()
    loader.read_text.side_effect = OSError("Read failed")

    data = {"$include": "file.yaml"}
    with pytest.raises(ValueError, match="Failed to load reference"):
        _resolve_includes(data, jail, loader)


# 4. load_flow_from_file custom root mismatch
def test_load_flow_custom_root_mismatch(tmp_path: Path) -> None:
    # File at /tmp/flow.yaml, root at /etc
    # This forces relative_to to fail -> triggers `except ValueError`

    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text("kind: LinearFlow\nmetadata:\n  name: A\n  version: 1.0.0\n  description: d\nsequence: []")

    # We need a fake root that is NOT a parent
    # But ManifestIO will be init with root_dir.
    # ManifestIO.read_text joins root_dir and path.
    # If load_path became absolute (file_path.name), it might fail read_text if ManifestIO expects relative?
    # ManifestIO uses (self.root_dir / path).read_text().
    # If path is filename "flow.yaml", it reads root_dir/flow.yaml.
    # If root_dir is unrelated, it won't find the file.

    # We can mock ManifestIO to succeed reading even if path logic weird.

    other_root = tmp_path / "other"
    other_root.mkdir()

    with patch("coreason_manifest.utils.loader.ManifestIO") as mock_io_cls:
        mock_loader = mock_io_cls.return_value
        mock_loader.read_text.return_value = (
            "kind: LinearFlow\nmetadata:\n  name: A\n  version: 1.0.0\n  description: d\nsequence: []"
        )

        # This will trigger the ValueError in relative_to, setting load_path = file_path.name
        load_flow_from_file(str(flow_file), root_dir=other_root)

        # Verify read_text called with just filename
        mock_loader.read_text.assert_called_with(flow_file.name)


# 5. load_agent_from_ref invalid format
def test_load_agent_invalid_ref_format(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid reference format"):
        load_agent_from_ref("module_class", root_dir=tmp_path)


# 6. load_agent_from_ref escape
def test_load_agent_escape(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()

    # Create file outside jail so resolve(strict=True) succeeds
    outside = tmp_path / "outside.py"
    outside.write_text("class Agent: pass")
    outside.chmod(0o600)

    with pytest.raises(SecurityJailViolationError, match="escapes the root directory"):
        load_agent_from_ref("../outside.py:Agent", root_dir=jail)


# 7. load_agent_from_ref not found
def test_load_agent_not_found(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    with pytest.raises(ValueError, match="Agent file not found"):
        load_agent_from_ref("missing.py:Agent", root_dir=jail)


# 8. load_agent_from_ref execution error
def test_load_agent_exec_fail(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    bad_agent = jail / "bad.py"
    bad_agent.write_text("raise RuntimeError('Boom')")
    bad_agent.chmod(0o600)

    with pytest.raises(RuntimeError, match="Boom"):
        load_agent_from_ref("bad.py:Agent", root_dir=jail)


# 9. load_agent_from_ref class missing
def test_load_agent_class_missing(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    good_agent = jail / "good.py"
    good_agent.write_text("class Other: pass")
    good_agent.chmod(0o600)

    with pytest.raises(ValueError, match="Agent class 'Agent' not found"):
        load_agent_from_ref("good.py:Agent", root_dir=jail)




def test_load_agent_exec_fail_cleanup_deps(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()

    # Create a dependency
    (jail / "dep.py").write_text("x = 1")
    (jail / "dep.py").chmod(0o600)

    # Create agent that imports dep then fails
    agent = jail / "agent_fail.py"
    agent.write_text("import dep\nraise RuntimeError('Fail')")
    agent.chmod(0o600)

    with pytest.raises(RuntimeError, match="Fail"):
        load_agent_from_ref("agent_fail.py:Agent", root_dir=jail)

    # Verify dep is cleaned up?
    # actually sys.modules is global.
    # But SandboxedPathFinder names it _jail_hash.dep.
    # We can't easily check sys.modules for absence without knowing the hash.
    # But this test ensures the loop runs.


def test_loader_package_success(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    pkg = jail / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("x = 1")

    finder = SandboxedPathFinder()
    with sandbox_context(jail):
        spec = finder.find_spec("mypkg")
        assert spec is not None
        assert spec.origin == str(pkg / "__init__.py")


def test_load_agent_not_a_class(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    jail.mkdir()
    agent_file = jail / "not_class.py"
    agent_file.write_text("Agent = 'I am not a class'")
    agent_file.chmod(0o600)

    with pytest.raises(TypeError, match="is not a class"):
        load_agent_from_ref("not_class.py:Agent", root_dir=jail)
