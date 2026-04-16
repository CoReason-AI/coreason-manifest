# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for StrEnum comparison operators and properties."""

from hypothesis import given, settings
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    RiskLevelPolicy,
    SemanticClassificationProfile,
    TensorStructuralFormatProfile,
)

# ---------------------------------------------------------------------------
# SemanticClassificationProfile lattice comparisons
# ---------------------------------------------------------------------------

ALL_CLASSIFICATIONS = list(SemanticClassificationProfile)


class TestSemanticClassificationProfile:
    """Exercise all comparison operators and clearance_level property."""

    @given(st.sampled_from(ALL_CLASSIFICATIONS))
    @settings(max_examples=10, deadline=None)
    def test_clearance_level_is_int(self, sc: SemanticClassificationProfile) -> None:
        assert isinstance(sc.clearance_level, int)
        assert 0 <= sc.clearance_level <= 3

    def test_ordering_hierarchy(self) -> None:
        pub = SemanticClassificationProfile.PUBLIC
        internal = SemanticClassificationProfile.INTERNAL
        conf = SemanticClassificationProfile.CONFIDENTIAL
        res = SemanticClassificationProfile.RESTRICTED

        assert pub < internal < conf < res
        assert res > conf > internal > pub
        assert pub <= pub
        assert res >= res
        assert pub <= internal
        assert res >= conf

    @given(st.sampled_from(ALL_CLASSIFICATIONS), st.sampled_from(ALL_CLASSIFICATIONS))
    @settings(max_examples=20, deadline=None)
    def test_le_ge_reflexive(self, a: SemanticClassificationProfile, b: SemanticClassificationProfile) -> None:
        if a.clearance_level <= b.clearance_level:
            assert a <= b
            assert b >= a
        else:
            assert a > b
            assert b < a

    def test_comparison_with_non_enum_returns_not_implemented(self) -> None:
        sc = SemanticClassificationProfile.PUBLIC
        assert sc.__lt__("not_an_enum") is NotImplemented
        assert sc.__le__("not_an_enum") is NotImplemented
        assert sc.__gt__(42) is NotImplemented
        assert sc.__ge__(42) is NotImplemented


# ---------------------------------------------------------------------------
# RiskLevelPolicy comparisons
# ---------------------------------------------------------------------------

ALL_RISKS = list(RiskLevelPolicy)


class TestRiskLevelPolicy:
    """Exercise all comparison operators and weight property."""

    @given(st.sampled_from(ALL_RISKS))
    @settings(max_examples=10, deadline=None)
    def test_weight_is_int(self, r: RiskLevelPolicy) -> None:
        assert isinstance(r.weight, int)
        assert 0 <= r.weight <= 2

    def test_weight_values(self) -> None:
        assert RiskLevelPolicy.SAFE.weight == 0
        assert RiskLevelPolicy.STANDARD.weight == 1
        assert RiskLevelPolicy.CRITICAL.weight == 2

    def test_ordering_hierarchy(self) -> None:
        safe = RiskLevelPolicy.SAFE
        std = RiskLevelPolicy.STANDARD
        crit = RiskLevelPolicy.CRITICAL

        assert safe < std < crit
        assert crit > std > safe
        assert safe <= safe
        assert crit >= crit

    @given(st.sampled_from(ALL_RISKS), st.sampled_from(ALL_RISKS))
    @settings(max_examples=15, deadline=None)
    def test_le_ge_consistency(self, a: RiskLevelPolicy, b: RiskLevelPolicy) -> None:
        if a.weight <= b.weight:
            assert a <= b
            assert b >= a

    def test_comparison_with_non_enum_returns_not_implemented(self) -> None:
        r = RiskLevelPolicy.SAFE
        assert r.__lt__("x") is NotImplemented
        assert r.__le__("x") is NotImplemented
        assert r.__gt__(42) is NotImplemented
        assert r.__ge__(42) is NotImplemented


# ---------------------------------------------------------------------------
# TensorStructuralFormatProfile bytes_per_element
# ---------------------------------------------------------------------------

ALL_TENSORS = list(TensorStructuralFormatProfile)


class TestTensorStructuralFormatProfile:
    """Verify bytes_per_element property for all tensor formats."""

    @given(st.sampled_from(ALL_TENSORS))
    @settings(max_examples=10, deadline=None)
    def test_bytes_per_element_is_positive_int(self, t: TensorStructuralFormatProfile) -> None:
        bpe = t.bytes_per_element
        assert isinstance(bpe, int)
        assert bpe > 0

    def test_specific_byte_sizes(self) -> None:
        assert TensorStructuralFormatProfile.FLOAT32.bytes_per_element == 4
        assert TensorStructuralFormatProfile.FLOAT64.bytes_per_element == 8
        assert TensorStructuralFormatProfile.INT8.bytes_per_element == 1
        assert TensorStructuralFormatProfile.UINT8.bytes_per_element == 1
        assert TensorStructuralFormatProfile.INT32.bytes_per_element == 4
        assert TensorStructuralFormatProfile.INT64.bytes_per_element == 8
