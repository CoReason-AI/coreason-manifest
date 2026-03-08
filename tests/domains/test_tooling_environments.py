import pytest
from pydantic import ValidationError

from coreason_manifest.tooling.environments import EphemeralNamespacePartition


def test_ephemeral_partition_temporal_override_proof() -> None:
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        EphemeralNamespacePartition(
            partition_id="part-1",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["a" * 64],
            max_ttl_seconds=0,  # INVALID: Triggers guillotine override check
            max_vram_mb=500,
        )


def test_ephemeral_partition_supply_chain_proof() -> None:
    with pytest.raises(ValidationError, match="Invalid SHA-256 hash in whitelist"):
        EphemeralNamespacePartition(
            partition_id="part-1",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["a" * 64, "invalid-hash-string"],  # INVALID
            max_ttl_seconds=300,
            max_vram_mb=500,
        )
