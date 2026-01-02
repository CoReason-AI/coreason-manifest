# Prosperity-3.0
from __future__ import annotations


class ManifestError(Exception):
    """Base exception for coreason_manifest errors."""

    pass


class ManifestSyntaxError(ManifestError):
    """Raised when the manifest YAML is invalid or missing required fields."""

    pass


class PolicyViolationError(ManifestError):
    """Raised when the agent violates a compliance policy."""

    def __init__(self, message: str, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class IntegrityCompromisedError(ManifestError):
    """Raised when the source code hash does not match the manifest."""

    pass
