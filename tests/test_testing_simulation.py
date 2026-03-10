# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import GenerativeManifoldSLA, SyntheticGenerationProfile


def test_generative_manifold_sla_valid() -> None:
    sla = GenerativeManifoldSLA(
        max_topological_depth=10,
        max_node_fanout=50,
        max_synthetic_tokens=100000,
    )
    assert sla.max_topological_depth == 10

    profile = SyntheticGenerationProfile(
        profile_id="sim_123",
        manifold_sla=sla,
        target_schema_ref="AnyTopology",
    )
    assert profile.target_schema_ref == "AnyTopology"


def test_generative_manifold_sla_geometric_explosion() -> None:
    with pytest.raises(ValidationError, match="Geometric explosion risk"):
        GenerativeManifoldSLA(
            max_topological_depth=50,
            max_node_fanout=50,  # 50 * 50 = 2500 > 1000
            max_synthetic_tokens=100000,
        )
