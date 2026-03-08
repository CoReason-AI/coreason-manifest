# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file defines the presentation intent grammar. This is a STRICTLY PROJECTION BOUNDARY.
These schemas govern how multi-dimensional agent knowledge is collapsed and encoded for human perception.
YOU ARE EXPLICITLY FORBIDDEN from adding state-mutation or backend logic here.
Think purely in terms of declarative graphical grammars (Marks, Channels, Scales).
"""

from typing import Annotated, Any, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.presentation.scivis import MacroGrid


class BaseIntent(CoreasonBaseModel):
    """Base class for presentation intents."""


class FYIIntent(BaseIntent):
    """Intent indicating the presentation is informational only."""

    type: Literal["fyi"] = Field(default="fyi", description="Discriminator for an FYI intent.")


class InformationalIntent(CoreasonBaseModel):
    type: Literal["informational"] = Field(
        default="informational", description="Discriminator for read-only informational handoffs."
    )
    message: str = Field(description="The context or summary to display to the human operator.")
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The orchestrator's automatic fallback if the human does not acknowledge the intent in time."
    )


class DraftingIntent(CoreasonBaseModel):
    type: Literal["drafting"] = Field(
        default="drafting", description="Discriminator for requesting specific missing context from a human."
    )
    context_prompt: str = Field(description="The prompt explaining what information the swarm is missing.")
    resolution_schema: dict[str, Any] = Field(
        description="The strict JSON Schema the human's input must satisfy before the graph can resume."
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The action to take if the human fails to provide the draft."
    )


class AdjudicationIntent(CoreasonBaseModel):
    type: Literal["forced_adjudication"] = Field(
        default="forced_adjudication", description="Discriminator for breaking deadlocks within a CouncilTopology."
    )
    deadlocked_claims: list[str] = Field(
        min_length=2, description="The conflicting claim IDs or proposals the human must choose between."
    )
    resolution_schema: dict[str, Any] = Field(
        description="The strict JSON Schema for the tie-breaking response (usually an enum of the deadlocked_claims)."
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The action to take if the oracle is unresponsive."
    )


class EscalationIntent(CoreasonBaseModel):
    type: Literal["escalation"] = Field(
        default="escalation", description="Discriminator for security or economic boundary overrides."
    )
    tripped_rule_id: str = Field(
        description="The ID of the Data Loss Prevention (DLP) or Governance rule that blocked execution."
    )
    resolution_schema: dict[str, Any] = Field(
        description="The strict JSON Schema requiring an explicit cryptographic "
        "sign-off or justification string to bypass the breaker."
    )
    timeout_action: Literal["rollback", "proceed_default", "terminate"] = Field(
        description="The default action is usually terminate or rollback for security escalations."
    )


type AnyPresentationIntent = Annotated[
    InformationalIntent | DraftingIntent | AdjudicationIntent | EscalationIntent, Field(discriminator="type")
]

# Provide backwards compatibility for AnyIntent, which tests might still refer
# to via PresentationEnvelope if not changed there, or __init__.py
type AnyIntent = AnyPresentationIntent


class PresentationEnvelope(CoreasonBaseModel):
    """An envelope wrapping a grid presentation and its intent."""

    intent: AnyPresentationIntent = Field(description="The reason an agent is presenting this data to a human.")
    grid: MacroGrid = Field(description="The grid of panels being presented.")
