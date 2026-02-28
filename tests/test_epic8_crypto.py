from datetime import UTC, datetime

from coreason_manifest.spec.interop.telemetry import CryptographicSignature, NodeExecution, NodeState


def test_cryptographic_signature() -> None:
    now = datetime.now(UTC)
    sig = CryptographicSignature(
        signature_scheme="ed25519", public_key="pubkey123", signature_value="sigvalue123", signed_at=now
    )
    assert sig.signature_scheme == "ed25519"  # noqa: S101
    assert sig.public_key == "pubkey123"  # noqa: S101
    assert sig.signature_value == "sigvalue123"  # noqa: S101
    assert sig.signed_at == now  # noqa: S101


def test_node_execution_signature() -> None:
    now = datetime.now(UTC)
    sig = CryptographicSignature(signature_scheme="rsa", public_key="pubkey", signature_value="sig", signed_at=now)

    exec_record = NodeExecution(
        node_id="n1", state=NodeState.COMPLETED, inputs={}, outputs={}, timestamp=now, duration_ms=10.0, signature=sig
    )

    assert exec_record.signature is not None  # noqa: S101
    assert exec_record.signature.signature_scheme == "rsa"  # noqa: S101
