# Prosperity-3.0
"""Exceptions for the Coreason Manifest system.

This module defines the hierarchy of exceptions raised by the package.
"""

from __future__ import annotations


class ManifestError(Exception):
    """Base exception for coreason_manifest errors."""

    pass


class ManifestSyntaxError(ManifestError):
    """Raised when the manifest YAML is invalid or missing required fields.

    This includes YAML parsing errors and JSON Schema validation failures.
    """

    pass


class PolicyViolationError(ManifestError):
    """Raised when the agent violates a compliance policy.

    This error indicates that the manifest is structurally valid but fails
    business rules or compliance checks (e.g., banned libraries).

    Attributes:
        violations: A list of specific policy violation messages.
    """

    def __init__(self, message: str, violations: list[str] | None = None) -> None:
        """Initialize PolicyViolationError.

        Args:
            message: The error message.
            violations: Optional list of detailed violation strings.
        """
        super().__init__(message)
        self.violations = violations or []


class IntegrityCompromisedError(ManifestError):
    """Raised when the source code hash does not match the manifest.

    This indicates that the source code may have been tampered with or changed
    without updating the manifest's integrity hash.
    """

    pass
