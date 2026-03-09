import pytest
from pydantic import ValidationError

from coreason_manifest.state.tensors import NDimensionalTensorManifest, TensorDType


def test_valid_tensor_manifest() -> None:
    """Verify standard valid 3D tensor passes cryptographic and topological checks."""
    manifest = NDimensionalTensorManifest(
        dtype=TensorDType.FLOAT32,
        shape=(512, 512, 3),
        memory_footprint_bytes=512 * 512 * 3 * 4,
        merkle_root="a" * 64,
        storage_uri="s3://secure-bucket/scan.raw",
    )
    assert manifest.shape == (512, 512, 3)


def test_invalid_tensor_memory_mismatch() -> None:
    """Verify that buffer-overflow vectors fail compile-time math checks."""
    with pytest.raises(ValidationError, match="Topological mismatch"):
        NDimensionalTensorManifest(
            dtype=TensorDType.FLOAT32,
            shape=(100, 100),
            memory_footprint_bytes=999999999,  # Intentional mismatch
            merkle_root="a" * 64,
            storage_uri="ipfs://data",
        )


def test_invalid_tensor_negative_dimension() -> None:
    """Verify non-euclidean geometry is rejected."""
    with pytest.raises(ValidationError, match="strictly positive integers"):
        NDimensionalTensorManifest(
            dtype=TensorDType.INT8,
            shape=(100, -5, 10),
            memory_footprint_bytes=100 * -5 * 10 * 1,
            merkle_root="a" * 64,
            storage_uri="ipfs://data",
        )
