# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import base64
import copy
import math
import struct
from typing import Any, cast

from hypothesis import given, settings
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    OntologicalAlignmentPolicy,
            TamperFaultEvent,
    VectorEmbeddingState,
)
from coreason_manifest.utils.algebra import calculate_latent_alignment











@given(
    st.lists(st.floats(allow_nan=True, allow_infinity=True, width=32), min_size=1, max_size=1000),
    st.lists(st.floats(allow_nan=True, allow_infinity=True, width=32), min_size=1, max_size=1000),
)
@settings(max_examples=1000, deadline=None)
def test_calculate_latent_alignment_fuzz(v1_floats: list[float], v2_floats: list[float]) -> None:
    dim = len(v1_floats)
    if len(v2_floats) > dim:
        v2_floats = v2_floats[:dim]
    elif len(v2_floats) < dim:
        v2_floats = v2_floats + [0.0] * (dim - len(v2_floats))

    v1_packed = struct.pack(f"<{dim}f", *v1_floats)
    v2_packed = struct.pack(f"<{dim}f", *v2_floats)

    v1 = VectorEmbeddingState(
        vector_base64=base64.b64encode(v1_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
    )
    v2 = VectorEmbeddingState(
        vector_base64=base64.b64encode(v2_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
    )

    policy = OntologicalAlignmentPolicy.model_construct(
        min_cosine_similarity=-1.0,
        require_isometry_proof=True,
    )

    try:
        sim = calculate_latent_alignment(v1, v2, policy)
        assert not math.isnan(sim), "Similarity should never be NaN"
        assert -1.0001 <= sim <= 1.0001, f"Cosine similarity out of bounds: {sim}"
    except ValueError:
        pass
    except TamperFaultEvent:
        pass


def test_calculate_latent_alignment_edge_cases() -> None:
    dim = 2
    policy = OntologicalAlignmentPolicy.model_construct(
        min_cosine_similarity=-1.0,
        require_isometry_proof=True,
    )

    # Clamping tests for precision drift
    # Force dot product to be very large via mocking or edge case values

    import unittest.mock

    with unittest.mock.patch("numpy.dot") as mock_dot:
        # Force dot_product > mag1 * mag2 (so similarity > 1.0)
        mock_dot.return_value = 1.1
        with unittest.mock.patch("numpy.linalg.norm", return_value=1.0):
            v1_packed = struct.pack(f"<{dim}f", 1.0, 0.0)
            v2_packed = struct.pack(f"<{dim}f", 1.0, 0.0)
            v1 = VectorEmbeddingState(
                vector_base64=base64.b64encode(v1_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
            )
            v2 = VectorEmbeddingState(
                vector_base64=base64.b64encode(v2_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
            )
            assert calculate_latent_alignment(v1, v2, policy) == 1.0

    with unittest.mock.patch("numpy.dot") as mock_dot:
        # Force dot_product < -mag1 * mag2 (so similarity < -1.0)
        mock_dot.return_value = -1.1
        with unittest.mock.patch("numpy.linalg.norm", return_value=1.0):
            v1_packed = struct.pack(f"<{dim}f", 1.0, 0.0)
            v2_packed = struct.pack(f"<{dim}f", -1.0, 0.0)
            v1 = VectorEmbeddingState(
                vector_base64=base64.b64encode(v1_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
            )
            v2 = VectorEmbeddingState(
                vector_base64=base64.b64encode(v2_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
            )
            assert calculate_latent_alignment(v1, v2, policy) == -1.0

    with unittest.mock.patch("numpy.dot") as mock_dot:
        # Force similarity to be NaN by returning float('nan') for dot_product
        mock_dot.return_value = float("nan")
        with unittest.mock.patch("numpy.linalg.norm", return_value=1.0):
            v1_packed = struct.pack(f"<{dim}f", 1.0, 0.0)
            v2_packed = struct.pack(f"<{dim}f", 1.0, 0.0)
            v1 = VectorEmbeddingState(
                vector_base64=base64.b64encode(v1_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
            )
            v2 = VectorEmbeddingState(
                vector_base64=base64.b64encode(v2_packed).decode(), dimensionality=dim, foundation_matrix_name="fuzz"
            )
            assert calculate_latent_alignment(v1, v2, policy) == 0.0

    # Also force the return from similarity division to be exactly NaN without failing the early check
    # e.g., if mag1=0 or mag2=0 is bypassed but similarity calculates to nan. This is impossible without mock,
    # since we check for mag1 == 0.0 and mag2 == 0.0 explicitly. We will test the math.isnan branch in code
    # by ensuring we execute it.

    # 4. Try sending something that bypasses magnitude checks but gives dot product NaN
    # We already did this via ValueError in our patch. Let's adjust the ValueError check
    # to only check mag1_sq and mag2_sq for NaN, and allow dot_product to be NaN for division.
