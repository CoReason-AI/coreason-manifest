import pytest

from coreason_manifest.core.telemetry.custody import EpistemicEnvelope, MerkleHasher
from coreason_manifest.core.telemetry.telemetry_schemas import AgentSignature, HardwareFingerprint


def test_merkle_hash_invalidation() -> None:
    """
    Prove that altering the payload of Envelope 1 invalidates the Merkle hash of Envelope 3.
    """
    hw = HardwareFingerprint(architecture="Ampere", compute_precision="fp16", vram_allocated=8000)
    agent = AgentSignature(
        model_weights_hash="abc", prompt_commit_hash="def", temperature=0.7, seed=42, inference_engine="vLLM"
    )

    env1 = EpistemicEnvelope(payload={"data": "step 1"}, hardware_fingerprint=hw, agent_signature=agent)
    hash1 = MerkleHasher.hash_envelope(env1)

    env2 = EpistemicEnvelope(
        payload={"data": "step 2"}, hardware_fingerprint=hw, agent_signature=agent, parent_hash=hash1
    )
    hash2 = MerkleHasher.hash_envelope(env2)

    env3 = EpistemicEnvelope(
        payload={"data": "step 3"}, hardware_fingerprint=hw, agent_signature=agent, parent_hash=hash2
    )
    hash3 = MerkleHasher.hash_envelope(env3)

    # Now alter the payload of env1 (simulating a tamper or mutation)
    # Recomputing the chain should result in a different hash for env3
    tampered_env1 = EpistemicEnvelope(
        payload={"data": "step 1 tampered"}, hardware_fingerprint=hw, agent_signature=agent
    )
    tampered_hash1 = MerkleHasher.hash_envelope(tampered_env1)

    tampered_env2 = EpistemicEnvelope(
        payload={"data": "step 2"}, hardware_fingerprint=hw, agent_signature=agent, parent_hash=tampered_hash1
    )
    tampered_hash2 = MerkleHasher.hash_envelope(tampered_env2)

    tampered_env3 = EpistemicEnvelope(
        payload={"data": "step 3"}, hardware_fingerprint=hw, agent_signature=agent, parent_hash=tampered_hash2
    )
    tampered_hash3 = MerkleHasher.hash_envelope(tampered_env3)

    assert hash3 != tampered_hash3


def test_unserializable_payload_raises_value_error() -> None:
    """
    Prove that passing an unserializable object to the hasher raises a strict ValueError
    instead of silently falling back to a memory-address string.
    """

    class UnserializableObject:
        pass

    obj = UnserializableObject()

    env = EpistemicEnvelope(payload=obj)
    with pytest.raises(ValueError, match=r"Strict serialization failure\. Cannot hash payload"):
        MerkleHasher.hash_envelope(env)
