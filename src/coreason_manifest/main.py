# Prosperity-3.0
"""Main module for coreason_manifest.

This module is primarily used for testing and demonstration purposes.
"""

from coreason_manifest.utils.logger import logger


def hello_world() -> str:
    """Returns a hello world string.

    Returns:
        "Hello World!" string.
    """
    logger.info("Hello World!")
    return "Hello World!"
