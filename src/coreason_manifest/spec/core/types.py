# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Any, TypeAlias

from pydantic import BeforeValidator, Field, field_serializer, model_validator

from coreason_manifest.spec.common_base import CoreasonModel

# =========================================================================
#  DOMAIN VOCABULARY (Living Standard)
# =========================================================================

# Strict Semantic Versioning (X.Y.Z)
SemanticVersion = Annotated[
    str,
    Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="A semantic version string (e.g., '1.0.0').",
        examples=["1.0.0", "0.1.0", "2.12.5"],
    ),
]

# Git SHA-1 Hash
GitSHA = Annotated[
    str,
    Field(
        pattern=r"^[a-f0-9]{40}$",
        description="A full 40-character Git SHA-1 hash.",
        examples=["a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"],
        min_length=40,
        max_length=40,
    ),
]

# Node Identifiers (Must be URL-safe, no spaces)
NodeID = Annotated[
    str,
    Field(
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="Unique identifier for a node in the graph. Alphanumeric, underscores, hyphens only.",
        examples=["agent_1", "start-node", "MyNode"],
    ),
]

# Variable Identifiers (Must be valid Python identifiers or close to it)
VariableID = Annotated[
    str,
    Field(
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
        min_length=1,
        max_length=64,
        description="Identifier for a variable in the blackboard. Must be a valid identifier format.",
        examples=["user_input", "result_data", "_internal_state"],
    ),
]

# Tool Identifiers
ToolID = Annotated[
    str,
    Field(
        min_length=1,
        description="Identifier for a tool or capability.",
        examples=["calculator", "web_search"],
    ),
]


# Middleware Identifiers (Alphanumeric, underscores, hyphens only)
MiddlewareID = Annotated[
    str,
    Field(
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=64,
        description="Identifier for a middleware component. Alphanumeric, underscores, and hyphens only.",
        examples=["pii_redactor", "security-filter"],
    ),
]


# Risk Level
class RiskLevel(StrEnum):
    """
    Risk classification for governance.
    Order matters: safe < standard < critical.
    """

    SAFE = "safe"
    STANDARD = "standard"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        if self == RiskLevel.SAFE:
            return 0
        if self == RiskLevel.STANDARD:
            return 1
        # RiskLevel.CRITICAL
        return 2


# Profile Identifiers
ProfileID = Annotated[
    str,
    Field(
        min_length=1,
        description="Identifier for a cognitive profile.",
        examples=["default_assistant", "code_expert"],
    ),
]


def _coerce_comma_strings(v: Any) -> Any:
    """Coerces 'a, b' into ['a', 'b'] before strict validation."""
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return v


# Apply this to all fields expecting lists of strings (like tags, tools, capabilities)
CoercibleStringList = Annotated[
    list[str],
    BeforeValidator(_coerce_comma_strings),
    Field(default_factory=list),
]


# Strict JSON Types
type StrictJson = (
    bool
    | int
    | float
    | str
    | list[StrictJson]
    | tuple[StrictJson, ...]
    | dict[str, StrictJson]
    | Mapping[str, StrictJson]
    | None
)


class StrictPayload(CoreasonModel):
    """Strict container for arbitrary JSON payloads."""

    data: Mapping[str, StrictJson] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _freeze_content(self) -> "StrictPayload":
        def _freeze(obj: Any) -> Any:
            if isinstance(obj, dict):
                return MappingProxyType({k: _freeze(v) for k, v in obj.items()})
            if isinstance(obj, list):
                return tuple(_freeze(v) for v in obj)
            return obj

        if isinstance(self.data, dict):
            # Enforce immutability on the dict itself
            object.__setattr__(self, "data", _freeze(self.data))
        return self

    @field_serializer("data")
    def serialize_data(self, v: Mapping[str, StrictJson], _info: Any) -> dict[str, Any]:
        return dict(v)


class MiddlewareDef(CoreasonModel):
    """
    Definition for a middleware component.
    """

    ref: str = Field(
        ...,
        pattern=r"^.*\.py:[a-zA-Z_][a-zA-Z0-9_]*$",
        description="Reference to the Python file and class (e.g., 'filters.py:PIIRedactor').",
    )
    config: dict[str, StrictJson] = Field(default_factory=dict, description="Initialization configuration.")
