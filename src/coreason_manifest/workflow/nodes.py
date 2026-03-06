# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.oversight.intervention import InterventionPolicy
from coreason_manifest.workflow.policies import (
    EpistemicScanner as EpistemicScanner,
    SelfCorrectionPolicy as SelfCorrectionPolicy,
    System1Reflex as System1Reflex,
)


class BaseNode(CoreasonBaseModel):
    """
    Base configuration for any execution node in a topology.
    """

    description: str = Field(description="A description of the node's function.")
    intervention_policies: list[InterventionPolicy] = Field(
        default_factory=list,
        description="A declarative list of proactive oversight hooks bound to this node's lifecycle.",
    )


class AgentNode(BaseNode):
    """
    A node representing an autonomous agent.
    """

    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
    action_space_id: str | None = Field(
        default=None, description="The ID of the specific ActionSpace (curated tool environment) bound to this agent."
    )
    reflex_policy: System1Reflex | None = Field(
        default=None, description="The policy governing System 1 reflex actions."
    )
    epistemic_policy: EpistemicScanner | None = Field(
        default=None, description="The policy governing epistemic scanning."
    )
    correction_policy: SelfCorrectionPolicy | None = Field(
        default=None, description="The policy governing self-correction loops."
    )


class HumanNode(BaseNode):
    """
    A node representing a human participant in the workflow.
    """

    type: Literal["human"] = Field(default="human", description="Discriminator for a Human node.")


class SystemNode(BaseNode):
    """
    A node representing a deterministic system capability.
    """

    type: Literal["system"] = Field(default="system", description="Discriminator for a System node.")


type AnyNode = Annotated[
    AgentNode | HumanNode | SystemNode,
    Field(
        discriminator="type",
        description="A discriminated union of all valid workflow nodes.",
    ),
]
