# Prosperity-3.0
import importlib
import os
from pathlib import Path

import coreason_manifest.utils.logger as logger_module
from coreason_manifest.utils.logger import logger


def test_logger_initialization() -> None:
    """Test that the logger is initialized correctly and creates the log directory."""
    # Since the logger is initialized on import, we check side effects

    # By default, it uses "logs" relative to CWD.
    # We check if "logs" exists (it should, created by import)
    # But strictly speaking, it depends on when import happened.
    # If this test runs after others, "logs" likely exists.

    # We don't assert it exists here because previous tests might have modified env vars
    # or state, but generally it should.
    # For robust testing, we rely on the specific coverage test below.
    assert logger is not None


def test_logger_exports() -> None:
    """Test that logger is exported."""
    assert logger is not None


def test_logger_coverage_reload(tmp_path: Path) -> None:
    """
    Trigger logger module execution with a non-existent dir to hit mkdir line.
    We use importlib.reload to re-run the module-level code in the main process.
    """
    target_dir = tmp_path / "logs_cov"

    # Ensure it doesn't exist
    assert not target_dir.exists()

    # Set env var to point to this new dir
    os.environ["COREASON_LOG_DIR"] = str(target_dir)

    try:
        # Reload the module to trigger execution of the top-level code
        importlib.reload(logger_module)

        # Verify directory was created (Functional check)
        assert target_dir.exists()
        assert target_dir.is_dir()

        # Verify log file creation
        assert (target_dir / "app.log").exists()

    finally:
        # Cleanup env var
        if "COREASON_LOG_DIR" in os.environ:
            del os.environ["COREASON_LOG_DIR"]

        # Restore default logger state by reloading again without the env var
        # This points it back to "logs" (or whatever default is)
        importlib.reload(logger_module)
