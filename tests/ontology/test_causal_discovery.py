# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Tests for causal discovery and estimation classes."""

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CausalDiscoveryIntent,
    CausalDiscoveryReceipt,
    DoWhyEstimationIntent,
    DoWhyEstimationReceipt,
    EconMLCATEIntent,
    HTEEstimationReceipt,
    StructuralCausalGraphProfile,
)


class TestCausalDiscoveryIntent:
    def test_instantiation(self) -> None:
        intent = CausalDiscoveryIntent(
            dataset_uri="s3://bucket/data.csv",
            discovery_algorithm="PC",
            max_discrete_bins=20,
        )
        assert intent.dataset_uri == "s3://bucket/data.csv"
        assert intent.discovery_algorithm == "PC"
        assert intent.max_discrete_bins == 20
        assert intent.topology_class == "causal_discovery_intent"

    def test_max_discrete_bins_validation(self) -> None:
        with pytest.raises(ValidationError):
            CausalDiscoveryIntent(
                dataset_uri="s3://bucket/data.csv",
                discovery_algorithm="PC",
                max_discrete_bins=101,  # le=100
            )


class TestStructuralCausalGraphProfile:
    def test_instantiation_and_sorting(self) -> None:
        profile = StructuralCausalGraphProfile(
            edges=[("B", "C"), ("A", "B")],
            nodes=["C", "A", "B"],
        )
        # Verify canonical sorting
        assert profile.edges == [("A", "B"), ("B", "C")]
        assert profile.nodes == ["A", "B", "C"]
        assert profile.topology_class == "structural_causal_graph"


class TestDoWhyEstimationIntent:
    def test_instantiation(self) -> None:
        graph = StructuralCausalGraphProfile(edges=[("X", "Y")], nodes=["X", "Y"])
        intent = DoWhyEstimationIntent(
            causal_graph=graph,
            treatment="X",
            outcome="Y",
        )
        assert intent.treatment == "X"
        assert intent.outcome == "Y"
        assert intent.causal_graph.edges == [("X", "Y")]


class TestDoWhyEstimationReceipt:
    def test_instantiation(self) -> None:
        receipt = DoWhyEstimationReceipt(
            identified_estimand="Estimand summary",
            average_treatment_effect=0.5,
            refutation_p_value=0.05,
        )
        assert receipt.average_treatment_effect == 0.5
        assert receipt.refutation_p_value == 0.05

    def test_p_value_validation(self) -> None:
        with pytest.raises(ValidationError):
            DoWhyEstimationReceipt(
                identified_estimand="test",
                average_treatment_effect=0.5,
                refutation_p_value=1.1,  # le=1.0
            )


class TestEconMLCATEIntent:
    def test_instantiation_and_sorting(self) -> None:
        base_receipt = DoWhyEstimationReceipt(
            identified_estimand="estimand",
            average_treatment_effect=0.5,
            refutation_p_value=0.05,
        )
        intent = EconMLCATEIntent(
            base_estimation_receipt=base_receipt,
            features=["Z2", "Z1"],
        )
        assert intent.features == ["Z1", "Z2"]
        assert intent.base_estimation_receipt.average_treatment_effect == 0.5


class TestCausalDiscoveryReceipt:
    def test_instantiation(self) -> None:
        graph = StructuralCausalGraphProfile(edges=[("A", "B")], nodes=["A", "B"])
        receipt = CausalDiscoveryReceipt(
            causal_graph=graph,
            discovery_algorithm_used="PC",
        )
        assert receipt.causal_graph.nodes == ["A", "B"]
        assert receipt.discovery_algorithm_used == "PC"


class TestHTEEstimationReceipt:
    def test_instantiation_and_sorting(self) -> None:
        receipt = HTEEstimationReceipt(
            features=["age", "income"],
            cate_estimate=0.25,
        )
        assert receipt.features == ["age", "income"]
        assert receipt.cate_estimate == 0.25
        
        receipt_unsorted = HTEEstimationReceipt(
            features=["income", "age"],
            cate_estimate=0.25,
        )
        assert receipt_unsorted.features == ["age", "income"]
