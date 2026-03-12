import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import NDimensionalTensorManifest, TensorStructuralFormatProfile


def test_n_dimensional_tensor_manifest_valid() -> None:
    # float32 is 4 bytes per element. 2 * 3 * 4 = 24 bytes
    manifest = NDimensionalTensorManifest(
        structural_type=TensorStructuralFormatProfile.FLOAT32,
        shape=(2, 3),
        vram_footprint_bytes=24,
        merkle_root="a" * 64,
        storage_uri="s3://bucket/tensor.bin",
    )
    assert manifest.vram_footprint_bytes == 24


def test_n_dimensional_tensor_manifest_empty_shape() -> None:
    with pytest.raises(ValidationError, match="Tensor shape must have at least 1 dimension"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(),
            vram_footprint_bytes=0,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin",
        )


def test_n_dimensional_tensor_manifest_negative_dimension() -> None:
    with pytest.raises(ValidationError, match="Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, -3),
            vram_footprint_bytes=24,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin",
        )


def test_n_dimensional_tensor_manifest_zero_dimension() -> None:
    with pytest.raises(ValidationError, match="Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 0),
            vram_footprint_bytes=0,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin",
        )


def test_n_dimensional_tensor_manifest_footprint_mismatch() -> None:
    # 2 * 3 * 4 = 24 bytes, but manifest declares 20
    with pytest.raises(
        ValidationError,
        match=r"Topological mismatch: Shape \(2, 3\) of float32 requires 24 bytes, but manifest declares 20 bytes",
    ):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 3),
            vram_footprint_bytes=20,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin",
        )
