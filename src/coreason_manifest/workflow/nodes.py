# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the orchestration node schemas. This is a STRICTLY TOPOLOGICAL BOUNDARY.
These schemas dictate the multi-agent graph geometry and decentralized routing mechanics. DO NOT inject procedural
execution code or synchronous blocking loops. Think purely in terms of graph theory, Byzantine fault tolerance, and
multi-agent market dynamics."""

from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import Field, field_validator

from coreason_manifest.compute.inference import ActiveInferenceContract, AnalogicalMappingTask, InterventionalCausalTask
from coreason_manifest.compute.peft import PeftAdapterContract
from coreason_manifest.compute.profiles import RoutingFrontier
from coreason_manifest.compute.stochastic import LogitSteganographyContract
from coreason_manifest.compute.symbolic import NeuroSymbolicHandoff
from coreason_manifest.compute.test_time import EscalationContract, ProcessRewardContract
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.identity import VerifiableCredentialPresentation
from coreason_manifest.oversight.dlp import SecureSubSession
from coreason_manifest.state.cognition import CognitiveStateProfile

if TYPE_CHECKING:
    from coreason_manifest.workflow.topologies import AnyTopology

from coreason_manifest.oversight.audit import MechanisticAuditContract
from coreason_manifest.oversight.governance import AnchoringPolicy
from coreason_manifest.oversight.intervention import InterventionPolicy
from coreason_manifest.workflow.constraints import InputMapping, OutputMapping


class BaseNode(CoreasonBaseModel):
    """
    Base configuration for any execution node in a topology.
    """

    description: str = Field(description="A description of the node's function.")
    architectural_intent: str | None = Field(
        default=None, description="The AI's declarative rationale for selecting this node."
    )
    justification: str | None = Field(
        default=None, description="Cryptographic/audit justification for this node's existence in the graph."
    )
    intervention_policies: list[InterventionPolicy] = Field(
        default_factory=list,
        description="A declarative list of proactive oversight hooks bound to this node's lifecycle.",
    )
    domain_extensions: dict[str, Any] | None = Field(
        default=None,
        description="Passive, untyped extension point for vertical domain context. "
        "Strictly bounded to prevent JSON-bomb memory leaks.",
    )

    @field_validator("domain_extensions", mode="before")
    @classmethod
    def validate_domain_extensions_depth(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("domain_extensions must be a dictionary")

        def _check_depth(obj: Any, depth: int) -> None:
            if depth > 5:
                raise ValueError("domain_extensions exceeds maximum allowed depth of 5")
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if not isinstance(key, str):
                        raise ValueError("domain_extensions keys must be strings")
                    if len(key) > 255:
                        raise ValueError("domain_extensions key exceeds maximum length of 255 characters")
                    _check_depth(val, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    _check_depth(item, depth + 1)
            else:
                # EXPLICIT LEAF NODE ENFORCEMENT: Prevent JSON serialization crashes
                if obj is not None and not isinstance(obj, (str, int, float, bool)):
                    raise ValueError(f"domain_extensions leaf values must be JSON primitives, got {type(obj).__name__}")

        _check_depth(v, 0)
        return v


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
    credential_presentations: list[VerifiableCredentialPresentation] = Field(
        default_factory=list,
        description="The wallet of selective disclosure credentials proving the agent's identity, clearance, "
        "and budget authorization.",
    )


class AgentNode(BaseNode):
    """
    A node representing an autonomous agent.
    """

    type: Literal["agent"] = Field(default="agent", description="Discriminator for an Agent node.")
    logit_steganography: LogitSteganographyContract | None = Field(
        default=None,
        description="The cryptographic contract forcing this agent to embed an undeniable provenance signature "
        "into its generative token stream.",
    )
    compute_frontier: RoutingFrontier | None = Field(
        default=None, description="The dynamic spot-market compute requirements for this agent."
    )
    peft_adapters: list[PeftAdapterContract] = Field(
        default_factory=list,
        description="A declarative list of ephemeral PEFT/LoRA weights required to be hot-swapped "
        "during this agent's execution.",
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
    active_inference_policy: ActiveInferenceContract | None = Field(
        default=None,
        description="The formal contract demanding mathematical proof of Expected Information Gain "
        "before authorizing tool execution.",
    )
    analogical_policy: AnalogicalMappingTask | None = Field(
        default=None, description="The formal contract forcing the agent to execute cross-domain lateral thinking."
    )
    interventional_policy: InterventionalCausalTask | None = Field(
        default=None,
        description="The formal contract authorizing the agent to mutate variables to prove Pearlian causation.",
    )
    symbolic_handoff_policy: NeuroSymbolicHandoff | None = Field(
        default=None,
        description="The API-like contract allowing the agent to offload rigid logic to deterministic CPU solvers.",
    )
    audit_policy: MechanisticAuditContract | None = Field(
        default=None,
        description="The adaptive trigger policy for executing deep mechanistic interpretability "
        "brain-scans on this agent.",
    )
    anchoring_policy: AnchoringPolicy | None = Field(
        default=None,
        description="The declarative contract mathematically binding this agent to a core altruistic objective.",
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
    topology: "AnyTopology" = Field(description="The encapsulated subgraph to execute.")
    input_mappings: list[InputMapping] = Field(default_factory=list, description="Explicit state projection inputs.")
    output_mappings: list[OutputMapping] = Field(default_factory=list, description="Explicit state projection outputs.")


# =========================================================================
# AGENT INSTRUCTION: WARNING - POLYMORPHIC ROUTER
# If you create a new class above, you MUST append it to the AnyNode union below.
# Failure to do so will result in a fatal Pydantic discriminator crash at runtime,
# creating a 'Dangling Class' that the orchestrator cannot deserialize.
# =========================================================================

type AnyNode = Annotated[
    AgentNode | HumanNode | SystemNode | CompositeNode,
    Field(
        discriminator="type",
        description="A discriminated union of all valid workflow nodes.",
    ),
]
