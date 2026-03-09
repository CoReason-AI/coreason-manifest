import pytest
from pydantic import ValidationError

from coreason_manifest.state.toolchains import BrowserDOMState


def test_browser_dom_ssrf_rejects_cloud_metadata() -> None:
    with pytest.raises(ValidationError, match="SSRF mathematical bound"):
        BrowserDOMState(
            current_url="http://169.254.169.254/iam/credentials",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )


def test_browser_dom_ssrf_rejects_localhost_variants() -> None:
    with pytest.raises(ValidationError, match="SSRF topological"):
        BrowserDOMState(
            current_url="http://localhost:3000",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )

    with pytest.raises(ValidationError, match="SSRF mathematical bound"):
        BrowserDOMState(
            current_url="http://127.0.0.1:5432",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )


def test_browser_dom_accepts_global_routable() -> None:
    # Should not raise
    state = BrowserDOMState(
        current_url="https://github.com/coreason-ai",
        viewport_size=(800, 600),
        dom_hash="a" * 64,
        accessibility_tree_hash="a" * 64,
    )
    assert state.current_url == "https://github.com/coreason-ai"


def test_browser_dom_accepts_global_ip() -> None:
    # Coverage for line returning url after IP checks (Line 66)
    state = BrowserDOMState(
        current_url="https://8.8.8.8/search",
        viewport_size=(800, 600),
        dom_hash="a" * 64,
        accessibility_tree_hash="a" * 64,
    )
    assert state.current_url == "https://8.8.8.8/search"


def test_browser_dom_accepts_no_hostname() -> None:
    # Coverage for line returning url when there is no hostname (Line 45)
    state = BrowserDOMState(
        current_url="about:blank", viewport_size=(800, 600), dom_hash="a" * 64, accessibility_tree_hash="a" * 64
    )
    assert state.current_url == "about:blank"
from coreason_manifest.state.toolchains import TerminalBufferState


def test_terminal_state_rejects_unix_absolute_path() -> None:
    with pytest.raises(ValidationError, match="Absolute Unix/Windows root paths"):
        # Provide dummy data for other required fields as dictated by the schema
        TerminalBufferState(working_directory="/etc/shadow", stdout_hash="", stderr_hash="", env_variables_hash="")


def test_terminal_state_rejects_windows_absolute_path() -> None:
    with pytest.raises(ValidationError, match="Windows drive letter"):
        TerminalBufferState(
            working_directory="C:\\Windows\\System32", stdout_hash="", stderr_hash="", env_variables_hash=""
        )


def test_terminal_state_rejects_traversal_sequences() -> None:
    with pytest.raises(ValidationError, match="Path traversal sequences"):
        TerminalBufferState(
            working_directory="../../var/log/syslog", stdout_hash="", stderr_hash="", env_variables_hash=""
        )


def test_terminal_state_accepts_safe_relative_path() -> None:
    state = TerminalBufferState(
        working_directory="local_scripts/runner", stdout_hash="", stderr_hash="", env_variables_hash=""
    )
    assert state.working_directory == "local_scripts/runner"
