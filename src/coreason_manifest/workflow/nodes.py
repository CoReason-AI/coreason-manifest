from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class BaseNode(CoreasonBaseModel):
    """
    Base configuration for any execution node in a topology.
    """

    description: str = Field(description="A description of the node's function.")


class System1Reflex(CoreasonBaseModel):
    """
    Policy for fast, intuitive system 1 thinking.
    """

    confidence_threshold: float = Field(description="The confidence threshold required to execute a reflex action.")
    allowed_read_only_tools: list[str] = Field(description="List of read-only tools allowed during a reflex action.")


class EpistemicScanner(CoreasonBaseModel):
    """
    Policy for epistemic scanning and gap detection.
    """

    active: bool = Field(description="Whether the epistemic scanner is active.")
    dissonance_threshold: float = Field(
        description="The threshold for cognitive dissonance before triggering an action."
    )
    action_on_gap: Literal["fail", "probe", "clarify"] = Field(
        description="The action to take when an epistemic gap is detected."
    )


class SelfCorrectionPolicy(CoreasonBaseModel):
    """
    Policy for self-correction and iterative refinement.
    """

    max_loops: int = Field(description="The maximum number of self-correction loops allowed.")
    rollback_on_failure: bool = Field(description="Whether to rollback to the previous state on failure.")


class AgentNode(BaseNode):
    """
    A node representing an autonomous agent.
    """

    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
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
