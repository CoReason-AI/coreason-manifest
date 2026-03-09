import pytest
from pydantic import ValidationError

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
