import base64

import pytest

from coreason_manifest.spec.ontology import (
    OntologicalAlignmentPolicy,
    VectorEmbeddingState,
)
from coreason_manifest.utils.algebra import (
    calculate_latent_alignment,
    verify_ast_safety,
)


def test_verify_ast_safety_slice() -> None:
    payload = "[1, 2, 3][0:2]"
    assert verify_ast_safety(payload)


def test_verify_ast_safety_forbidden() -> None:
    payload = "[x for x in range(10)]"  # List comprehension isn't in base_allowlist
    with pytest.raises(ValueError, match="Kinetic execution bleed detected"):
        verify_ast_safety(payload)


def test_calculate_latent_alignment_struct_error() -> None:
    v1 = VectorEmbeddingState(
        model_name="test-model", dimensionality=1000, vector_base64=base64.b64encode(b"not enough data").decode()
    )
    v2 = VectorEmbeddingState(
        model_name="test-model", dimensionality=1000, vector_base64=base64.b64encode(b"not enough data").decode()
    )
    policy = OntologicalAlignmentPolicy(min_cosine_similarity=0.5, require_isometry_proof=False)
    with pytest.raises(ValueError, match="Byte length does not match declared dimensionality"):
        calculate_latent_alignment(v1, v2, policy)
