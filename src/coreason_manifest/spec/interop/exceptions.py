from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FaultSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    RECOVERABLE = "RECOVERABLE"
    WARNING = "WARNING"
    INFO = "INFO"


class RecoveryAction(StrEnum):
    HALT = "HALT_GRAPH"
    RETRY = "PROMPT_RETRY"
    SKIP = "SKIP_NODE"
    IGNORE = "IGNORE"


class SemanticFault(BaseModel):
    """
    Immutable error state envelope.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    error_code: str
    message: str
    severity: FaultSeverity
    recovery_action: RecoveryAction
    context: dict[str, Any] = Field(default_factory=dict)


class ManifestError(Exception):
    """
    Base exception for Coreason Manifest.
    Backed by a SemanticFault model.
    """

    def __init__(self, fault: SemanticFault) -> None:
        self.fault = fault
        super().__init__(fault.message)

    def __str__(self) -> str:
        return f"[{self.fault.error_code}] {self.fault.message} (Severity: {self.fault.severity})"


class SecurityJailViolationError(Exception):
    """
    Raised when a file operation attempts to escape the sandbox jail.
    Legacy exception retained for compatibility with loader.py.
    """
