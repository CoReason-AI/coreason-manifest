# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Annotated, Any, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID
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


class SystemFaultEvent(BaseStateEvent):
    type: Literal["system_fault"] = Field(
        default="system_fault", description="Discriminator type for a system fault event."
    )


type AnyStateEvent = Annotated[
    ObservationEvent | BeliefUpdateEvent | SystemFaultEvent,
    Field(discriminator="type", description="A discriminated union of state events."),
]
