# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable event schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm, modeling Atomic Semantic State Transitions.
YOU ARE EXPLICITLY FORBIDDEN from introducing mutable state loops, standard CRUD database paradigms,
or kinetic execution parameters. All memory must be modeled as an append-only, content-addressable Merkle-DAG.
Focus purely on cryptographic event sourcing, hardware attestations, and non-monotonic belief assertions
and retractions."""

from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
from coreason_manifest.state.cognition import CognitiveUncertaintyProfile
from coreason_manifest.state.embodied import EmbodiedSensoryVector
from coreason_manifest.state.scratchpad import LatentScratchpadTrace
from coreason_manifest.state.toolchains import AnyToolchainState


class BaseStateEvent(CoreasonBaseModel):
    event_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the Merkle-DAG."
    )
    timestamp: float = Field(description="Causal Ancestry markers required to resolve decentralized event ordering.")


class ZeroKnowledgeProof(CoreasonBaseModel):
    proof_protocol: Literal["zk-SNARK", "zk-STARK", "plonk", "bulletproofs"] = Field(
        description="The mathematical dialect of the cryptographic proof."
    )
    public_inputs_hash: str = Field(
        description="The SHA-256 hash of the public inputs (e.g., prompt, Lamport clock) "
        "anchoring this proof to the specific state index."
    )
    verifier_key_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the public evaluation key."
    )
    cryptographic_blob: str = Field(
        max_length=5_000_000, description="The base64-encoded succinct cryptographic proof payload."
    )
    latent_state_commitments: dict[str, Annotated[str, StringConstraints(max_length=100)]] = Field(
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
    audit_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the Merkle-DAG.",
    )
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
        max_length=8192,
        description="The base64-encoded hardware quote signed by the silicon manufacturer's master private key.",
    )


class ObservationEvent(BaseStateEvent):
    type: Literal["observation"] = Field(
        default="observation", description="Discriminator type for an observation event."
    )
    payload: dict[str, Any] = Field(
        description="Neurosymbolic Bindings of the raw, lossless semantic output appended from "
        "the environment or tool execution that anchor statistical probability to a definitive causal event hash."
    )
    source_node_id: NodeID | None = Field(
        default=None, description="The specific topological node that appended this observation."
    )
    hardware_attestation: HardwareEnclaveAttestation | None = Field(
        default=None,
        description="The physical hardware root-of-trust proving this observation was appended in a secure enclave.",
    )
    zk_proof: ZeroKnowledgeProof | None = Field(
        default=None, description="The mathematical attestation proving this observation was appended securely."
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
        description="The mathematical brain-scan proving exactly which neural circuits fired to append this event.",
    )
    triggering_invocation_id: str | None = Field(
        default=None,
        description="The Event ID of the specific ToolInvocationEvent that spawned this observation, "
        "forming a strict bipartite directed edge.",
    )


class ToolInvocationEvent(BaseStateEvent):
    """A Priori Kinetic Commitment representing the Pearlian Do-Operator prior to network execution."""

    type: Literal["tool_invocation"] = Field(
        default="tool_invocation", description="Discriminator type for a tool invocation event."
    )
    tool_name: str = Field(description="The exact tool targeted in the ActionSpace.")
    parameters: dict[str, Any] = Field(description="The intended JSON-RPC payload.")
    authorized_budget_cents: int | None = Field(
        default=None, ge=0, description="The maximum escrow unlocked for this specific run."
    )


class CausalAttribution(CoreasonBaseModel):
    source_event_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the source event in the Merkle-DAG."
    )
    influence_weight: float = Field(
        ge=0.0,
        le=1.0,
        description="The mathematical attention/importance weight (0.0 to 1.0) assigned to this source by the agent.",
    )


class BeliefUpdateEvent(BaseStateEvent):
    type: Literal["belief_update"] = Field(
        default="belief_update", description="Discriminator type for a Belief Assertion event."
    )
    payload: dict[str, Any] = Field(
        description="Topologically Bounded Latent Spaces capturing the semantic representation "
        "of the agent's internal cognitive shift or synthesis that anchor statistical probability "
        "to a definitive causal event hash."
    )
    source_node_id: NodeID | None = Field(
        default=None, description="The specific topological node that synthesized this belief assertion."
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
        description="The mathematical attestation proving this belief synthesis was appended "
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
        description="The mathematical brain-scan proving exactly which neural circuits fired to append this event.",
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

    task_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this causal intervention to the Merkle-DAG."
    )
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
    condition_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this falsification test to the Merkle-DAG.",
    )
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
    hypothesis_id: str = Field(
        min_length=1,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this abductive leap to the Merkle-DAG.",
    )
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
    target_event_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the active node generation cycle that was killed in the Merkle-DAG."
    )
    sensory_trigger: EmbodiedSensoryVector | None = Field(
        default=None,
        description="The continuous multimodal trigger (e.g., audio spike, user saying 'stop') "
        "that justified the interruption.",
    )
    retained_partial_payload: dict[str, Any] | str | None = Field(
        default=None,
        description="The 'stutter' state: the incomplete fragment of thought or text appended before the kill signal.",
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
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark "
        "linking this node to the specific historical state node where the agent mathematically "
        "diverged to simulate an alternative path."
    )
    counterfactual_intervention: str = Field(
        description="The specific alternative action or do-calculus intervention applied in the simulation."
    )
    expected_utility_actual: float = Field(
        description="The calculated utility of the trajectory that was actually executed."
    )
    expected_utility_simulated: float = Field(
        description="The calculated utility of the simulated counterfactual trajectory."
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


class EpistemicPromotionEvent(BaseStateEvent):
    type: Literal["epistemic_promotion"] = Field(
        default="epistemic_promotion", description="Discriminator type for an epistemic promotion event."
    )
    source_episodic_event_ids: list[str] = Field(
        description="A list of CIDs (Content Identifiers) representing the raw logs being compressed and archived."
    )
    crystallized_semantic_node_id: str = Field(
        description="The resulting permanent W3C DID / CID of the newly minted knowledge node."
    )
    compression_ratio: float = Field(
        description="A mathematical proof of the token savings achieved (e.g., old_token_count / new_token_count)."
    )


class NormativeDriftEvent(BaseStateEvent):
    type: Literal["normative_drift"] = Field(
        default="normative_drift", description="Discriminator type for a normative drift event."
    )
    tripped_rule_id: str = Field(
        description="The Content Identifier (CID) of the specific ConstitutionalRule causing logical friction."
    )
    measured_semantic_drift: float = Field(
        description="The calculated probabilistic delta showing how far the swarm's observed reality "
        "is diverging from the static rule."
    )
    contradiction_proof_hash: str = Field(
        description="A cryptographic pointer to the internal scratchpad trace (ThoughtBranch) "
        "definitively proving the rule is obsolete or causing a loop."
    )


class PersistenceCommitReceipt(BaseStateEvent):
    type: Literal["persistence_commit"] = Field(
        default="persistence_commit", description="Discriminator type for a persistence commit receipt."
    )
    lakehouse_snapshot_id: str = Field(
        min_length=1, description="The external cryptographic receipt generated by Iceberg/Delta."
    )
    committed_state_diff_id: str = Field(min_length=1, description="The internal StateDiff CID that was flushed.")
    target_table_uri: str = Field(min_length=1, description="The specific table mutated.")


class ActiveInferenceYield(BaseStateEvent):
    """
    AGENT INSTRUCTION: Terminal state node proving epistemic exhaustion.
    Must be emitted when internal probability distributions fall below safe execution thresholds.
    """

    type: Literal["active_inference_yield"] = Field(
        default="active_inference_yield", description="Discriminator type for an active inference yield event."
    )
    target_variable_urn: str = Field(..., description="Identifier of the missing structural parameter.")
    epistemic_confidence_delta: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quantified gap between current state confidence and required execution threshold.",
    )
    canonical_projection: str = Field(
        ..., description="Machine-to-human/oracle translation of the information deficit."
    )
    temporal_escalation_bound: int = Field(
        ..., gt=0, description="TTL/timeout parameter before autonomous fallback or system failure."
    )


# =========================================================================
# AGENT INSTRUCTION: WARNING - POLYMORPHIC ROUTER
# If you create a new class above, you MUST append it to the AnyStateEvent union below.
# Failure to do so will result in a fatal Pydantic discriminator crash at runtime,
# creating a 'Dangling Class' that the orchestrator cannot deserialize.
# =========================================================================

type AnyStateEvent = Annotated[
    ObservationEvent
    | BeliefUpdateEvent
    | SystemFaultEvent
    | HypothesisGenerationEvent
    | BargeInInterruptEvent
    | CounterfactualRegretEvent
    | ToolInvocationEvent
    | EpistemicPromotionEvent
    | NormativeDriftEvent
    | PersistenceCommitReceipt
    | ActiveInferenceYield,
    Field(discriminator="type", description="A discriminated union of state events."),
]
