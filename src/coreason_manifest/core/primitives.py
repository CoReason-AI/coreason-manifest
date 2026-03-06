# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from enum import StrEnum
from typing import Annotated

from pydantic import Field

# =========================================================================
#  DOMAIN VOCABULARY (Living Standard)
# =========================================================================

type SemanticVersion = Annotated[
    str,
    Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="A semantic version string (e.g., '1.0.0').",
        examples=["1.0.0", "0.1.0", "2.12.5"],
    ),
]

type GitSHA = Annotated[
    str,
    Field(
        pattern=r"^[a-f0-9]{40}$",
        description="A full 40-character Git SHA-1 hash.",
        examples=["a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"],
        min_length=40,
        max_length=40,
    ),
]

type NodeID = Annotated[
    str,
    Field(
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="Unique identifier for a node in the graph. Alphanumeric, underscores, hyphens only.",
        examples=["agent_1", "start-node", "MyNode"],
    ),
]

type ToolID = Annotated[
    str,
    Field(
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="Identifier for a tool or capability.",
        examples=["calculator", "web_search"],
    ),
]

type ProfileID = Annotated[
    str,
    Field(
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=128,
        description="Identifier for a cognitive profile.",
        examples=["default_assistant", "code_expert"],
    ),
]


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
        """Return the numeric weight corresponding to the risk level."""
        if self == RiskLevel.SAFE:
            return 0
        if self == RiskLevel.STANDARD:
            return 1
        return 2


class DataClassification(StrEnum):
    """
    Standardized Information Flow Control (IFC) clearance levels.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class SystemRole(StrEnum):
    """
    Standardized Persona-Based Access Control (PBAC) Roles.
    """

    SYSTEM_ADMIN = "system_admin"
    TENANT_ADMIN = "tenant_admin"
    AGENT_BUILDER = "agent_builder"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    VIEWER = "viewer"
    MACHINE_SERVICE = "machine_service"
