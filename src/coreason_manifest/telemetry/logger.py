# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""
AGENT INSTRUCTION: This module exposes the centralized, passive logger.
Per the Coreason Protocol, you are STRICTLY FORBIDDEN from configuring sinks
(e.g., logger dot add) or modifying execution state here.
"""

from loguru import logger

__all__ = ["logger"]
