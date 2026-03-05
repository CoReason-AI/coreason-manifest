# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import SemanticVersion

class ConstitutionalRule(CoreasonBaseModel):
    """
    Defines a constitutional rule for AI governance.
    """

    rule_id: str = Field(description="Unique identifier for the constitutional rule.")
    description: str = Field(description="Detailed description of the rule.")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level if the rule is violated."
    )
    forbidden_intents: set[Annotated[str, StringConstraints(min_length=1)]] = Field(
        description="List of intents that are forbidden by this rule."
    )


class GovernancePolicy(CoreasonBaseModel):
    """
    Defines a governance policy comprising multiple constitutional rules.
    """

    policy_name: str = Field(description="Name of the governance policy.")
    version: SemanticVersion = Field(description="Semantic version of the governance policy.")
    rules: list[ConstitutionalRule] = Field(description="List of constitutional rules included in this policy.")
