import math

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import NDimensionalTensorManifest, TensorStructuralFormatProfile


# 1. Fuzzing the Valid Mathematical Space
@given(
    structural_type=st.sampled_from(list(TensorStructuralFormatProfile)),
    shape=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5).map(tuple),
)
@settings(max_examples=100)
def test_n_dimensional_tensor_manifest_fuzz_valid(
    structural_type: TensorStructuralFormatProfile, shape: tuple[int, ...]
) -> None:
    """Mathematically prove the deterministic acceptance of correct spatial boundaries across infinite shapes."""
    expected_bytes = math.prod(shape) * structural_type.bytes_per_element

    manifest = NDimensionalTensorManifest(
        structural_type=structural_type,
        shape=shape,
        vram_footprint_bytes=expected_bytes,
        merkle_root="a" * 64,
        storage_uri="s3://bucket/tensor.bin",
    )
    assert manifest.vram_footprint_bytes == expected_bytes


# 2. Parameterizing Atomic Boundary Violations
@pytest.mark.parametrize(
    ("shape", "footprint", "match_string"),
    [
        ((), 0, "must have at least 1 dimension"),
        ((2, -3), 24, "strictly positive integers"),
        ((2, 0), 0, "strictly positive integers"),
        ((2, 3), 20, "Topological mismatch"),  # For float32 (4 bytes), requires 24
    ],
)
def test_n_dimensional_tensor_manifest_atomic_violations(
    shape: tuple[int, ...], footprint: int, match_string: str
) -> None:
    """Prove the physical bounds engine rejects mathematically impossible geometries."""
    with pytest.raises(ValidationError, match=match_string):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=shape,
            vram_footprint_bytes=footprint,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin",
        )
