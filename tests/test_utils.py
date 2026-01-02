# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_manifest

# We need to reload the module to test the initialization logic again
# because it runs at module level.
import importlib
import shutil
from pathlib import Path

from loguru import logger

from coreason_manifest.utils import logger as logger_module


def test_logger_initialization_creates_dir() -> None:
    """Test that the logger creates the log directory if it doesn't exist."""

    # Setup: Remove logs dir if exists
    log_path = Path("logs")

    # Ensure logger handlers are removed to release file locks on Windows
    logger.remove()

    if log_path.exists():
        shutil.rmtree(log_path)

    # Reload the module to trigger the top-level code
    importlib.reload(logger_module)

    assert log_path.exists()
    assert log_path.is_dir()


def test_logger_exports() -> None:
    """Test that logger is exported."""
    from coreason_manifest.utils.logger import logger

    assert logger is not None
