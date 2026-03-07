# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import Field

from coreason_manifest.compute.profiles import RoutingFrontier
from coreason_manifest.compute.test_time import EscalationContract, ProcessRewardContract
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.oversight.dlp import SecureSubSession
from coreason_manifest.state.cognition import CognitiveStateProfile

if TYPE_CHECKING:
    from coreason_manifest.workflow.topologies import AnyTopology

from coreason_manifest.oversight.intervention import InterventionPolicy
from coreason_manifest.workflow.constraints import InputMapping, OutputMapping


class BaseNode(CoreasonBaseModel):
    """
    Base configuration for any execution node in a topology.
    """

    description: str = Field(description="A description of the node's function.")
    intervention_policies: list[InterventionPolicy] = Field(
        default_factory=list,
        description="A declarative list of proactive oversight hooks bound to this node's lifecycle.",
    )


class System1Reflex(CoreasonBaseModel):
    """
    Policy for fast, intuitive system 1 thinking.
    """

    confidence_threshold: float = Field(
        ge=0.0, le=1.0, description="The confidence threshold required to execute a reflex action."
    )
    allowed_read_only_tools: list[str] = Field(description="List of read-only tools allowed during a reflex action.")


class EpistemicScanner(CoreasonBaseModel):
    """
    Policy for epistemic scanning and gap detection.
    """

    active: bool = Field(description="Whether the epistemic scanner is active.")
    dissonance_threshold: float = Field(
        ge=0.0, le=1.0, description="The threshold for cognitive dissonance before triggering an action."
    )
    action_on_gap: Literal["fail", "probe", "clarify"] = Field(
        description="The action to take when an epistemic gap is detected."
    )


class SelfCorrectionPolicy(CoreasonBaseModel):
    """
    Policy for self-correction and iterative refinement.
    """

    max_loops: int = Field(ge=0, le=50, description="The maximum number of self-correction loops allowed.")
    rollback_on_failure: bool = Field(description="Whether to rollback to the previous state on failure.")


class AgentAttestation(CoreasonBaseModel):
    """
    Cryptographic identity passport and AI-BOM for the agent.
    """

    training_lineage_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$", description="The exact SHA-256 Merkle root of the agent's training lineage."
    )
    developer_signature: str = Field(description="The cryptographic signature of the developer/vendor.")
    capability_merkle_root: str = Field(
        pattern=r"^[a-f0-9]{64}$", description="The SHA-256 Merkle root of the agent's verified semantic capabilities."
    )


class AgentNode(BaseNode):
    """
    A node representing an autonomous agent.
    """

    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
    compute_frontier: RoutingFrontier | None = Field(
        default=None, description="The dynamic spot-market compute requirements for this agent."
    )
    agent_attestation: AgentAttestation | None = Field(
        default=None, description="The cryptographic identity passport and AI-BOM for the agent."
    )
    action_space_id: str | None = Field(
        default=None, description="The ID of the specific ActionSpace (curated tool environment) bound to this agent."
    )
    secure_sub_session: SecureSubSession | None = Field(
        default=None,
        description="Declarative boundary for handling unredacted secrets "
        "within a temporarily isolated memory partition.",
    )
    baseline_cognitive_state: CognitiveStateProfile | None = Field(
        default=None,
        description="The default biochemical 'mood' simulated for this agent via Representation Engineering.",
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
    escalation_policy: EscalationContract | None = Field(
        default=None, description="The mathematical boundary authorizing the agent to spin up Test-Time Compute."
    )
    prm_policy: ProcessRewardContract | None = Field(
        default=None, description="The ruleset governing how intermediate thoughts are scored and pruned."
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


class CompositeNode(BaseNode):
    """
    A node that encapsulates a nested workflow topology.
    """

    type: Literal["composite"] = Field(default="composite", description="Discriminator for a Composite node.")
    topology: "AnyTopology" = Field(description="The encapsulated subgraph to execute.")  # noqa: UP037
    input_mappings: list[InputMapping] = Field(default_factory=list, description="Explicit state projection inputs.")
    output_mappings: list[OutputMapping] = Field(default_factory=list, description="Explicit state projection outputs.")


type AnyNode = Annotated[
    AgentNode | HumanNode | SystemNode | CompositeNode,
    Field(
        discriminator="type",
        description="A discriminated union of all valid workflow nodes.",
    ),
]
