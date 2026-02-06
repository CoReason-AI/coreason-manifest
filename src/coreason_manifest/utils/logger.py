# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import logging
import sys
from typing import Any

from loguru import logger

__all__ = ["configure_logging", "logger"]


class InterceptHandler(logging.Handler):
    """
    Redirect standard logging to Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2

        # Skip the current frame (InterceptHandler.emit) if possible
        if frame:
            frame = frame.f_back

        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
    intercept_standard_logging: bool = True,
    sink: Any = sys.stderr,
) -> None:
    """
    Configure the global logger.

    Args:
        level: Minimum log level (default: "INFO")
        json_format: Whether to output logs in JSON format (default: True)
        intercept_standard_logging: Whether to redirect standard logging to Loguru (default: True)
        sink: The output sink (default: sys.stderr)
    """
    # Remove default handler
    logger.remove()

    # Configure sink
    logger.add(sink, level=level, serialize=json_format)

    # Intercept standard logging
    if intercept_standard_logging:
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
