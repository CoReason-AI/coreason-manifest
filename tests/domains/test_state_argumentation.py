# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest import EnsembleTopologySpec, UtilityJustificationGraph


def test_ensemble_topology_literal_constraint() -> None:
    with pytest.raises(ValidationError):
        EnsembleTopologySpec(
            concurrent_branch_ids=["did:coreason:1", "did:coreason:2"],
            fusion_function="arbitrary_unsupported_string",  # type: ignore
        )


def test_utility_graph_interlocks() -> None:
    # Test valid
    valid_graph = UtilityJustificationGraph(
        superposition_variance_threshold=0.05,
        ensemble_spec=EnsembleTopologySpec(
            concurrent_branch_ids=["did:coreason:1", "did:coreason:2"],
            fusion_function="weighted_consensus",
        ),
    )
    assert valid_graph.superposition_variance_threshold == 0.05

    # Test threshold zero with ensemble fallback (Escrow Failure)
    with pytest.raises(ValidationError, match="Topological Interlock Failed"):
        UtilityJustificationGraph(
            superposition_variance_threshold=0.0,
            ensemble_spec=EnsembleTopologySpec(
                concurrent_branch_ids=["did:coreason:1", "did:coreason:2"],
                fusion_function="highest_confidence",
            ),
        )

    # Test tensor poisoning rejection
    with pytest.raises(ValidationError, match="Tensor Poisoning Detected"):
        UtilityJustificationGraph(
            optimizing_vectors={"epistemic_gain": float("nan")}, superposition_variance_threshold=0.1
        )
