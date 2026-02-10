# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum


class ErrorDomain(StrEnum):
    """Domains where errors can originate."""

    CLIENT = "client"
    SYSTEM = "system"
    LLM = "llm"
    TOOL = "tool"
    SECURITY = "security"


class CoreasonError(Exception):
    """Base class for all Coreason Manifest errors."""



class AgentNotFoundError(CoreasonError, ValueError):
    """Raised when an agent file or path does not exist."""



class InvalidReferenceError(CoreasonError, ValueError):
    """Raised when an agent reference string (e.g., 'file:var') is malformed."""



class AgentDefinitionError(CoreasonError, ValueError):
    """Raised when the loaded object is not of the expected type or cannot be defined."""



class SchemaConflictError(CoreasonError, ValueError):
    """Raised when merging capabilities results in incompatible JSON schemas."""



class NamingConventionWarning(UserWarning):
    """Warning for aggressive name sanitization."""
