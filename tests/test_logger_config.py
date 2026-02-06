# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import io
import json
import logging
from typing import Any

from loguru import logger

from coreason_manifest.utils.logger import configure_logging


def test_configure_logging_json() -> None:
    """Test that logging is configured to output JSON."""
    sink = io.StringIO()
    configure_logging(level="INFO", json_format=True, sink=sink, intercept_standard_logging=False)

    logger.info("Test message")

    output = sink.getvalue()
    log_data = json.loads(output)

    assert log_data["record"]["message"] == "Test message"
    assert log_data["record"]["level"]["name"] == "INFO"


def test_configure_logging_text() -> None:
    """Test that logging is configured to output text."""
    sink = io.StringIO()
    configure_logging(level="INFO", json_format=False, sink=sink, intercept_standard_logging=False)

    logger.info("Test message")

    output = sink.getvalue()
    assert "Test message" in output
    # loguru default format contains "INFO"
    assert "INFO" in output


def test_configure_logging_level() -> None:
    """Test that logging level is respected."""
    sink = io.StringIO()
    configure_logging(level="WARNING", json_format=True, sink=sink, intercept_standard_logging=False)

    logger.info("Info message")
    logger.warning("Warning message")

    output = sink.getvalue()
    assert "Info message" not in output
    assert "Warning message" in output


def test_intercept_standard_logging() -> None:
    """Test that standard logging is intercepted."""
    sink = io.StringIO()

    # Configure logging to intercept standard logging
    configure_logging(level="INFO", json_format=True, sink=sink, intercept_standard_logging=True)

    logging.info("Standard logging message")

    output = sink.getvalue()
    assert "Standard logging message" in output

    # Parse JSON to verify
    log_data = json.loads(output)
    assert log_data["record"]["message"] == "Standard logging message"

    # Reset logging handlers to avoid side effects
    logging.root.handlers = []


def test_intercept_custom_level() -> None:
    """Test interception of custom logging levels."""
    sink = io.StringIO()
    configure_logging(level="INFO", json_format=True, sink=sink, intercept_standard_logging=True)

    # Add a custom level
    CUSTOM_LEVEL = 25
    logging.addLevelName(CUSTOM_LEVEL, "CUSTOM")

    logging.log(CUSTOM_LEVEL, "Custom level message")

    output = sink.getvalue()
    log_data = json.loads(output)

    assert log_data["record"]["message"] == "Custom level message"
    assert log_data["record"]["level"]["name"] == "Level 25"

    logging.root.handlers = []
