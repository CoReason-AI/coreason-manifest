import contextlib
import errno
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.spec.core.flow import FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.governance import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    Governance,
    check_circuit,
    record_failure,
)
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.io import ManifestIO, SecurityViolationError
from coreason_manifest.utils.loader import load_agent_from_ref

# --- Governance Coverage ---


def test_circuit_breaker_timeout_logic() -> None:
    """Cover lines 125-126 and 129 in governance.py."""
    policy = CircuitBreaker(error_threshold_count=1, reset_timeout_seconds=2)
    state_store = {"node_1": CircuitState(state="open", failure_count=1, last_failure_time=time.time())}

    # Case 1: Timeout NOT expired
    with pytest.raises(CircuitOpenError):
        check_circuit("node_1", policy, state_store)

    # Case 2: Timeout EXPIRED
    # Force unwrap optional for test logic, or assert it's not None
    last_failure = state_store["node_1"].last_failure_time
    assert last_failure is not None
    state_store["node_1"].last_failure_time = last_failure - 3
    check_circuit("node_1", policy, state_store)
    assert state_store["node_1"].state == "half-open"


def test_circuit_breaker_record_failure_coverage() -> None:
    """Cover initialization and early return in record_failure."""
    policy = CircuitBreaker(error_threshold_count=2, reset_timeout_seconds=1)
    state_store: dict[str, CircuitState] = {}

    # 1. New Node (Init logic)
    record_failure("new_node", policy, state_store)
    assert "new_node" in state_store
    assert state_store["new_node"].failure_count == 1

    # 2. Open Circuit (Early return logic)
    # Trip it
    record_failure("new_node", policy, state_store)  # count=2 -> open
    assert state_store["new_node"].state == "open"
    last_fail = state_store["new_node"].last_failure_time

    # Call again - should return early and NOT update time or count
    time.sleep(0.1)
    record_failure("new_node", policy, state_store)
    assert state_store["new_node"].last_failure_time == last_fail  # Unchanged


# --- Gatekeeper Coverage ---


def test_gatekeeper_schemeless_url() -> None:
    """Cover line 93 in gatekeeper.py: schemeless URL handling."""
    # Define a tool with a schemeless URL
    tool = ToolCapability(
        name="schemeless_tool",
        description="A tool without schema",
        url="evil.com/api",  # No https://
        risk_level="standard",
    )

    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Schemeless Test", version="1.0", description="desc", tags=[]),
        definitions=FlowDefinitions(
            tool_packs={
                "pack1": ToolPack(kind="ToolPack", namespace="pack1", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        sequence=[],
        governance=Governance(allowed_domains=["good.com"]),  # evil.com should fail
    )

    reports = validate_policy(flow)

    # Should find a violation for evil.com
    violation = next((r for r in reports if "blocked domain" in r.message), None)
    assert violation is not None
    assert "evil.com" in violation.message


def test_gatekeeper_port_stripping() -> None:
    """Cover port stripping logic (line 93)."""
    tool = ToolCapability(
        name="port_tool",
        description="Tool with port",
        url="https://evil.com:8080/api",
        risk_level="standard",
    )

    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Port Test", version="1.0", description="desc", tags=[]),
        definitions=FlowDefinitions(
            tool_packs={
                "pack1": ToolPack(kind="ToolPack", namespace="pack1", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        sequence=[],
        governance=Governance(allowed_domains=["good.com"]),
    )

    reports = validate_policy(flow)
    violation = next((r for r in reports if "blocked domain" in r.message), None)
    assert violation is not None
    assert "evil.com" in violation.message  # Should be stripped of port


# --- IO Coverage ---


def test_manifest_io_eloop_enoent() -> None:
    """Cover lines 60-63 in io.py: ELOOP and ENOENT handling."""
    loader = ManifestIO(root_dir=Path("/tmp"))

    # Mock os.open to raise ELOOP
    with patch("os.open") as mock_open:
        mock_open.side_effect = OSError(errno.ELOOP, "Too many symlinks")
        with pytest.raises(SecurityViolationError) as exc_sec:
            loader.read_text("loop.txt")
        assert "Symlink detected" in str(exc_sec.value)

    # Mock os.open to raise ENOENT
    with patch("os.open") as mock_open:
        mock_open.side_effect = OSError(errno.ENOENT, "No such file")
        with pytest.raises(FileNotFoundError):
            loader.read_text("missing.txt")

    # Mock os.open to raise EACCES (other error)
    with patch("os.open") as mock_open:
        mock_open.side_effect = OSError(errno.EACCES, "Permission denied")
        with pytest.raises(OSError, match="Permission denied") as exc_os:
            loader.read_text("locked.txt")
        assert exc_os.value.errno == errno.EACCES


# --- Loader Coverage ---


def test_loader_ast_import_from_banned(tmp_path: Path) -> None:
    """Cover line 103 in loader.py: banned 'from X import Y'."""
    file_path = tmp_path / "banned.py"
    file_path.write_text("from os import path\nclass Agent: pass")

    with pytest.raises(SecurityViolationError) as exc:
        load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)
    assert "Banned import 'os' detected" in str(exc.value)


def test_loader_ast_relative_import(tmp_path: Path) -> None:
    """Cover relative imports which have no node.module."""
    file_path = tmp_path / "relative.py"
    # 'from . import sibling' -> node.module is None
    file_path.write_text("from . import sibling\nclass Agent: pass")

    with contextlib.suppress(ValueError, ImportError, ModuleNotFoundError):
        load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)


def test_loader_banned_call(tmp_path: Path) -> None:
    """Cover banned calls like exec/eval."""
    file_path = tmp_path / "banned_call.py"
    file_path.write_text("class Agent:\n    def run(self): eval('1+1')")

    with pytest.raises(SecurityViolationError) as exc:
        load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)
    assert "Banned call 'eval'" in str(exc.value)


def test_loader_not_a_class(tmp_path: Path) -> None:
    """Cover line 211 failure case."""
    file_path = tmp_path / "not_class.py"
    file_path.write_text("NotAgent = 'just a string'")

    with pytest.raises(TypeError) as exc:
        load_agent_from_ref(f"{file_path.name}:NotAgent", root_dir=tmp_path)
    assert "is not a class" in str(exc.value)


def test_loader_success(tmp_path: Path) -> None:
    """Cover line 211 success case."""
    file_path = tmp_path / "good.py"
    file_path.write_text("class Agent:\n    pass")

    cls = load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)
    assert cls.__name__ == "Agent"
