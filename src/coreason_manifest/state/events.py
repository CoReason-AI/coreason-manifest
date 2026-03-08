# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable event schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or downstream business logic. Focus purely on cryptographic
event sourcing, hardware attestations, and non-monotonic belief updates."""

from typing import Annotated, Any, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
from coreason_manifest.state.cognition import CognitiveUncertaintyProfile
from coreason_manifest.state.embodied import EmbodiedSensoryVector
from coreason_manifest.state.scratchpad import LatentScratchpadTrace
from coreason_manifest.state.toolchains import AnyToolchainState


class BaseStateEvent(CoreasonBaseModel):
    event_id: str = Field(description="A unique identifier for the event.")
    timestamp: float = Field(description="The timestamp when the event occurred.")


class ZeroKnowledgeProof(CoreasonBaseModel):
    proof_protocol: Literal["zk-SNARK", "zk-STARK", "plonk", "bulletproofs"] = Field(
        description="The mathematical dialect of the cryptographic proof."
    )
    public_inputs_hash: str = Field(
        description="The SHA-256 hash of the public inputs (e.g., prompt, Lamport clock) "
        "anchoring this proof to the specific state index."
    )
    verifier_key_id: str = Field(
        description="The identifier of the public evaluation key the orchestrator must load to verify this proof."
    )
    cryptographic_blob: str = Field(description="The base64-encoded succinct cryptographic proof payload.")
    latent_state_commitments: dict[str, str] = Field(
        default_factory=dict,
        description="Cryptographic bindings (hashes) of intermediate residual stream states "
        "to prevent activation spoofing.",
    )


class SaeFeatureActivation(CoreasonBaseModel):
    feature_index: int = Field(
        ge=0,
        description="The exact dimensional index of the monosemantic feature in the Sparse Autoencoder dictionary.",
    )
    activation_magnitude: float = Field(
        description="The mathematical strength of this feature's activation during the forward pass."
    )
    interpretability_label: str | None = Field(
        default=None,
        description="The human-readable semantic concept mapped to this feature "
        "(e.g., 'sycophancy', 'truth_retrieval').",
    )


class NeuralAuditAttestation(CoreasonBaseModel):
    audit_id: str = Field(min_length=1, description="Unique identifier for this mechanistic interpretability snapshot.")
    layer_activations: dict[int, list[SaeFeatureActivation]] = Field(
        description="A mapping of specific transformer layer indices to their top-k activated SAE features."
    )
    causal_scrubbing_applied: bool = Field(
        default=False,
        description="Cryptographic proof that the orchestrator actively resampled or ablated this circuit "
        "to verify its causal responsibility for the output.",
    )


class HardwareEnclaveAttestation(CoreasonBaseModel):
    enclave_type: Literal["intel_tdx", "amd_sev_snp", "aws_nitro", "nvidia_cc"] = Field(
        description="The physical silicon architecture generating the root-of-trust quote."
    )
    platform_measurement_hash: str = Field(
        description="The cryptographic hash of the Platform Configuration Registers (PCRs) proving the memory state "
        "was physically isolated."
    )
    hardware_signature_blob: str = Field(
        description="The base64-encoded hardware quote signed by the silicon manufacturer's master private key."
    )


class ObservationEvent(BaseStateEvent):
    type: Literal["observation"] = Field(
        default="observation", description="Discriminator type for an observation event."
    )
    payload: dict[str, Any] = Field(
        description="The raw, lossless semantic output captured from the environment or tool execution."
    )
    source_node_id: NodeID | None = Field(
        default=None, description="The specific topological node that generated this observation."
    )
    hardware_attestation: HardwareEnclaveAttestation | None = Field(
        default=None,
        description="The physical hardware root-of-trust proving this observation was generated in a secure enclave.",
    )
    zk_proof: ZeroKnowledgeProof | None = Field(
        default=None, description="The mathematical attestation proving this observation was generated securely."
    )
    toolchain_snapshot: AnyToolchainState | None = Field(
        default=None,
        description="The immutable cryptographic snapshot of the external environment at the moment of observation.",
    )
    sensory_trigger: EmbodiedSensoryVector | None = Field(
        default=None,
        description="The continuous multimodal trigger that forced this discrete observation.",
    )
    neural_audit: NeuralAuditAttestation | None = Field(
        default=None,
        description="The mathematical brain-scan proving exactly which neural circuits fired to generate this event.",
    )


class CausalAttribution(CoreasonBaseModel):
    source_event_id: str = Field(description="The exact event ID in the EpistemicLedger that influenced this belief.")
    influence_weight: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical attention/importance weight (0.0 to 1.0) assigned to this source by the agent.",
    )


class BeliefUpdateEvent(BaseStateEvent):
    type: Literal["belief_update"] = Field(
        default="belief_update", description="Discriminator type for a belief update event."
    )
    payload: dict[str, Any] = Field(
        description="The semantic representation of the agent's internal cognitive shift or synthesis."
    )
    source_node_id: NodeID | None = Field(
        default=None, description="The specific topological node that synthesized this belief update."
    )
    causal_attributions: list[CausalAttribution] = Field(
        default_factory=list,
        description="Immutable audit trail of prior states that forced this specific cognitive synthesis.",
    )
    hardware_attestation: HardwareEnclaveAttestation | None = Field(
        default=None,
        description="The physical hardware root-of-trust proving this belief was synthesized in a secure enclave.",
    )
    zk_proof: ZeroKnowledgeProof | None = Field(
        default=None,
        description="The mathematical attestation proving this belief synthesis was generated "
        "securely without model-downgrade fraud.",
    )
    uncertainty_profile: CognitiveUncertaintyProfile | None = Field(
        default=None,
        description="The mathematical quantification of doubt associated with this synthesized belief.",
    )
    scratchpad_trace: LatentScratchpadTrace | None = Field(
        default=None,
        description="The cryptographic record of the non-monotonic internal monologue that justifies this belief.",
    )
    neural_audit: NeuralAuditAttestation | None = Field(
        default=None,
        description="The mathematical brain-scan proving exactly which neural circuits fired to generate this event.",
    )


class SystemFaultEvent(BaseStateEvent):
    type: Literal["system_fault"] = Field(
        default="system_fault", description="Discriminator type for a system fault event."
    )


class CausalDirectedEdge(CoreasonBaseModel):
    source_variable: str = Field(min_length=1, description="The independent variable $X$.")
    target_variable: str = Field(min_length=1, description="The dependent variable $Y$.")
    edge_type: Literal["direct_cause", "confounder", "collider", "mediator"] = Field(
        description="The specific Pearlian topological relationship between the two variables."
    )


class InterventionalCausalTask(CoreasonBaseModel):
    """A rigid do-calculus intervention forcing the agent to simulate a reality manipulation."""

    task_id: str = Field(description="Unique identifier for this causal intervention.")
    target_variable: str = Field(description="The dependent variable Y being measured.")
    do_operator_interventions: dict[str, Any] = Field(
        description="The strict do(X=x) topological amputations applied to the causal graph."
    )
    expected_information_gain: float = Field(
        ge=0.0, le=1.0, description="The calculated certainty bounded [0.0, 1.0] expected from this test."
    )


class StructuralCausalModel(CoreasonBaseModel):
    observed_variables: list[str] = Field(description="The nodes in the DAG that the agent can passively measure.")
    latent_variables: list[str] = Field(description="The unobserved confounders the agent suspects exist.")
    causal_edges: list[CausalDirectedEdge] = Field(description="The declared topological mapping of causality.")


class FalsificationCondition(CoreasonBaseModel):
    condition_id: str = Field(min_length=1, description="Unique identifier for this falsification test.")
    description: str = Field(
        description="Semantic description of what observation would prove the parent hypothesis is false."
    )
    required_tool_name: str | None = Field(
        default=None,
        description="The specific ActionSpace tool required to test this condition (e.g., 'sql_query_db').",
    )
    falsifying_observation_signature: str = Field(
        description="The expected data schema or regex pattern that, if returned by the tool, kills the hypothesis."
    )


class HypothesisGenerationEvent(BaseStateEvent):
    type: Literal["hypothesis"] = Field(
        default="hypothesis", description="Discriminator for a hypothesis generation event."
    )
    hypothesis_id: str = Field(min_length=1, description="Unique identifier for this abductive leap.")
    premise_text: str = Field(description="The natural language explanation of the abductive theory.")
    bayesian_prior: float = Field(
        ge=0.0,
        le=1.0,
        description="The agent's initial probabilistic belief in this hypothesis before testing.",
    )
    falsification_conditions: list[FalsificationCondition] = Field(
        min_length=1,
        description="The list of strict conditions that the orchestrator must test to attempt to "
        "disprove this premise.",
    )
    status: Literal["active", "falsified", "verified"] = Field(
        default="active", description="The current validity state of this hypothesis in the EpistemicLedger."
    )
    causal_model: StructuralCausalModel | None = Field(
        default=None,
        description="The formal DAG representing the agent's structural assumptions about the environment.",
    )


class BargeInInterruptEvent(BaseStateEvent):
    """A cryptographic receipt of a continuous multimodal sequence being prematurely severed by an external stimulus."""

    type: Literal["barge_in"] = Field(
        default="barge_in", description="Discriminator type for a barge-in interruption event."
    )
    target_event_id: str = Field(description="The exact event ID of the active node generation cycle that was killed.")
    sensory_trigger: EmbodiedSensoryVector | None = Field(
        default=None,
        description="The continuous multimodal trigger (e.g., audio spike, user saying 'stop') "
        "that justified the interruption.",
    )
    retained_partial_payload: dict[str, Any] | str | None = Field(
        default=None,
        description="The 'stutter' state: the incomplete fragment of thought or text generated before the kill signal.",
    )
    epistemic_disposition: Literal["discard", "retain_as_context", "mark_as_falsified"] = Field(
        description="Explicit instruction to the orchestrator on how to patch the shared memory blackboard "
        "with the partial payload."
    )


class CounterfactualRegretEvent(BaseStateEvent):
    """A cryptographic record of an agent simulating an alternative timeline to calculate epistemic regret
    and update its policy."""

    type: Literal["counterfactual_regret"] = Field(
        default="counterfactual_regret", description="Discriminator type for a counterfactual regret event."
    )
    historical_event_id: str = Field(
        description="The specific historical state node where the agent mathematically diverged "
        "to simulate an alternative path."
    )
    counterfactual_intervention: str = Field(
        description="The specific alternative action or do-calculus intervention applied in the simulation."
    )
    expected_utility_actual: float = Field(
        description="The computed utility of the trajectory that was actually executed."
    )
    expected_utility_simulated: float = Field(
        description="The computed utility of the simulated counterfactual trajectory."
    )
    epistemic_regret: float = Field(
        description="The mathematical variance (simulated - actual) representing the opportunity "
        "cost of the historical decision."
    )
    policy_update_gradients: dict[str, float] = Field(
        default_factory=dict,
        description="The stateless routing gradient adjustments derived from the calculated regret, "
        "used to self-correct future routing.",
    )


type AnyStateEvent = Annotated[
    ObservationEvent
    | BeliefUpdateEvent
    | SystemFaultEvent
    | HypothesisGenerationEvent
    | BargeInInterruptEvent
    | CounterfactualRegretEvent,
    Field(discriminator="type", description="A discriminated union of state events."),
]
