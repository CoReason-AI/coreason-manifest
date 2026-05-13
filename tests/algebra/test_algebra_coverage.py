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
import struct
import unittest.mock
from typing import Any

import pytest
from coreason_manifest.spec.ontology import (
    OntologicalAlignmentPolicy,
    VectorEmbeddingState,
)
from coreason_manifest.utils import algebra
from coreason_manifest.utils.algebra import (
    calculate_latent_alignment,
    compute_merkle_directory_cid,
    get_ontology_schema,
)


def test_get_ontology_schema_cached_object() -> None:
    # Trigger line 154 by setting _CACHED_ONTOLOGY_SCHEMA_BYTES to None
    # but _CACHED_ONTOLOGY_SCHEMA to something
    with (
        unittest.mock.patch.object(algebra, "_CACHED_ONTOLOGY_SCHEMA", {"test": "data"}),
        unittest.mock.patch.object(algebra, "_CACHED_ONTOLOGY_SCHEMA_BYTES", None),
    ):
        res = get_ontology_schema()
        assert res == {"test": "data"}


def test_calculate_latent_alignment_v2_invalid_base64() -> None:
    pol = OntologicalAlignmentPolicy(min_cosine_similarity=-1.0, require_isometry_proof=False)
    v1 = VectorEmbeddingState.model_construct(
        vector_base64=base64.b64encode(struct.pack("<3f", 1.0, 0.0, 0.0)).decode(),
        dimensionality=3,
        foundation_matrix_name="model1",
    )
    # v2 with invalid base64
    v2_invalid = VectorEmbeddingState.model_construct(
        vector_base64="a", dimensionality=3, foundation_matrix_name="model1"
    )

    with pytest.raises(ValueError, match=r"Topological Contradiction: Invalid base64 encoding\."):
        calculate_latent_alignment(v1, v2_invalid, pol)


def test_compute_merkle_directory_cid() -> None:
    files = {
        "file1.txt": b"content1",
        "file2.txt": b"content2",
    }
    cid = compute_merkle_directory_cid(files)
    assert cid.startswith("sha256:")
    assert len(cid) == 7 + 64

    # Verify determinism
    assert compute_merkle_directory_cid(files) == cid

    # Verify sorting
    files_swapped = {
        "file2.txt": b"content2",
        "file1.txt": b"content1",
    }
    assert compute_merkle_directory_cid(files_swapped) == cid
