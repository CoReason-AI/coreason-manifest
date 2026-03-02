import pytest

from coreason_manifest.core.common.suspense import SkeletonType, SuspenseConfig
from coreason_manifest.core.telemetry.custody import EpistemicEnvelope, MerkleHasher
from coreason_manifest.core.telemetry.suspense_envelope import StreamSuspenseEnvelope
from coreason_manifest.core.telemetry.telemetry_schemas import AgentSignature, HardwareFingerprint


@pytest.fixture
def base_hardware_fingerprint() -> HardwareFingerprint:
    return HardwareFingerprint(architecture="Ampere", compute_precision="fp8", vram_allocated=16.0)


@pytest.fixture
def base_agent_signature() -> AgentSignature:
    return AgentSignature(
        model_weights_hash="hash_a1", prompt_commit_hash="commit_xyz", temperature=0.7, seed=42, inference_engine="vLLM"
    )


def test_chain_of_custody_tamper_proof(
    base_hardware_fingerprint: HardwareFingerprint, base_agent_signature: AgentSignature
):
    """
    Chains three EpistemicEnvelopes together and proves that altering the payload
    of Envelope 1 invalidates the Merkle hash of Envelope 3.
    """
    # 1. Create first envelope
    payload_1 = {"extracted_text": "Medical claim 1"}
    hash_1 = MerkleHasher.compute_hash(base_agent_signature, payload_1, None)
    env_1 = EpistemicEnvelope(
        payload=payload_1,
        agent_signature=base_agent_signature,
        hardware_fingerprint=base_hardware_fingerprint,
        parent_envelope_hash=None,
        merkle_hash=hash_1,
    )

    # 2. Create second envelope (chained to first)
    payload_2 = {"parsed_claim": "Claim 1 implies X"}
    hash_2 = MerkleHasher.compute_hash(base_agent_signature, payload_2, env_1.merkle_hash)
    env_2 = EpistemicEnvelope(
        payload=payload_2,
        agent_signature=base_agent_signature,
        hardware_fingerprint=base_hardware_fingerprint,
        parent_envelope_hash=env_1.merkle_hash,
        merkle_hash=hash_2,
    )

    # 3. Create third envelope (chained to second)
    payload_3 = {"final_proposition": "X is True"}
    hash_3 = MerkleHasher.compute_hash(base_agent_signature, payload_3, env_2.merkle_hash)
    env_3 = EpistemicEnvelope(
        payload=payload_3,
        agent_signature=base_agent_signature,
        hardware_fingerprint=base_hardware_fingerprint,
        parent_envelope_hash=env_2.merkle_hash,
        merkle_hash=hash_3,
    )

    assert env_3.merkle_hash == hash_3

    # Now, simulate a tampering of envelope 1's payload
    tampered_payload_1 = {"extracted_text": "Medical claim 1 ALTERED"}
    tampered_hash_1 = MerkleHasher.compute_hash(base_agent_signature, tampered_payload_1, None)

    # If the system were to re-compute the hashes for the chain based on tampered_hash_1
    tampered_hash_2 = MerkleHasher.compute_hash(base_agent_signature, payload_2, tampered_hash_1)
    tampered_hash_3 = MerkleHasher.compute_hash(base_agent_signature, payload_3, tampered_hash_2)

    # The newly computed final hash should NOT match the original final hash
    assert tampered_hash_3 != env_3.merkle_hash


def test_suspense_envelope_captures_hardware(
    base_hardware_fingerprint: HardwareFingerprint, base_agent_signature: AgentSignature
):
    """
    Proves the SuspenseEnvelope correctly captures the HardwareFingerprint and related custody data.
    """
    payload = {"failed_extraction": "Blurry p-value"}
    merkle_hash = MerkleHasher.compute_hash(base_agent_signature, payload, None)

    epistemic_envelope = EpistemicEnvelope(
        payload=payload,
        agent_signature=base_agent_signature,
        hardware_fingerprint=base_hardware_fingerprint,
        parent_envelope_hash=None,
        merkle_hash=merkle_hash,
    )

    suspense_config = SuspenseConfig(fallback_type=SkeletonType.SPINNER)

    suspense_envelope = StreamSuspenseEnvelope(
        op="suspense_mount",
        p=suspense_config,
        timestamp=1620000000.0,
        reasoning_trace="Failed due to OCR confidence score < 0.2",
        epistemic_envelope=epistemic_envelope,
        hardware_fingerprint=base_hardware_fingerprint,
    )

    # Verify that the HardwareFingerprint is stored correctly inside the SuspenseEnvelope
    assert suspense_envelope.hardware_fingerprint is not None
    assert suspense_envelope.hardware_fingerprint.architecture == "Ampere"
    assert suspense_envelope.hardware_fingerprint.vram_allocated == 16.0

    # Also verify the chained epistemic envelope is intact
    assert suspense_envelope.epistemic_envelope is not None
    assert suspense_envelope.epistemic_envelope.merkle_hash == merkle_hash
