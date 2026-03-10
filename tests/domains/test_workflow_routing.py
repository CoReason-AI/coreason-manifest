# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest import BypassReceipt, DynamicRoutingManifest, GlobalSemanticProfile


def test_modality_alignment_raises_error() -> None:
    profile = GlobalSemanticProfile(artifact_event_id="some-id", detected_modalities=["text"], token_density=100)

    with pytest.raises(
        ValidationError,
        match=r"Cannot route to subgraph 'tabular_grid' because it is missing from detected_modalities.",
    ):
        DynamicRoutingManifest(
            manifest_id="manifest-1",
            artifact_profile=profile,
            active_subgraphs={"tabular_grid": ["did:web:worker1"]},
            bypassed_steps=[],
            branch_budgets_magnitude={},
        )


def test_conservation_of_custody_raises_error() -> None:
    profile = GlobalSemanticProfile(
        artifact_event_id="root-artifact-1", detected_modalities=["text"], token_density=100
    )

    bypass = BypassReceipt(
        artifact_event_id="other-artifact-2",
        bypassed_node_id="did:web:worker2",
        justification="modality_mismatch",
        cryptographic_null_hash="0" * 64,
    )

    with pytest.raises(
        ValidationError, match=r"BypassReceipt artifact_event_id does not match the root artifact_profile."
    ):
        DynamicRoutingManifest(
            manifest_id="manifest-1",
            artifact_profile=profile,
            active_subgraphs={"text": ["did:web:worker1"]},
            bypassed_steps=[bypass],
            branch_budgets_magnitude={},
        )
