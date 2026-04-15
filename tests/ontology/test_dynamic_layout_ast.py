# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for DynamicLayoutManifest AST validation."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import DynamicLayoutManifest


class TestDynamicLayoutManifest:
    """Exercise validate_tstring and enforce_ast_thermodynamic_gas_limit."""

    def test_valid_simple_string(self) -> None:
        obj = DynamicLayoutManifest(layout_tstring="Hello World")
        assert obj.layout_tstring == "Hello World"

    def test_valid_simple_name(self) -> None:
        """A simple Python identifier passes AST validation (Name node is allowed)."""
        obj = DynamicLayoutManifest(layout_tstring="user_name")
        assert obj.layout_tstring == "user_name"

    def test_valid_plain_python_literal(self) -> None:
        obj = DynamicLayoutManifest(layout_tstring="'hello'")
        assert obj.layout_tstring == "'hello'"

    def test_forbidden_set_literal(self) -> None:
        """Curly braces are parsed as Set literal, which is forbidden."""
        with pytest.raises(ValidationError, match="Forbidden AST node"):
            DynamicLayoutManifest(layout_tstring="{name}")

    def test_forbidden_binary_op(self) -> None:
        """Binary operations are forbidden."""
        with pytest.raises(ValidationError, match="Forbidden AST node"):
            DynamicLayoutManifest(layout_tstring="a + b")

    def test_ast_complexity_exceeded(self) -> None:
        """A template with too many AST nodes exceeds the gas limit."""
        heavy = "\n".join([f"x{i}" for i in range(200)])
        with pytest.raises(ValidationError, match="AST Complexity Overload"):
            DynamicLayoutManifest(layout_tstring=heavy, max_ast_node_budget=10)

    def test_custom_budget_low(self) -> None:
        obj = DynamicLayoutManifest(layout_tstring="x", max_ast_node_budget=5)
        assert obj.max_ast_node_budget == 5

    @given(
        text=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=50),
    )
    @settings(max_examples=15, deadline=None)
    def test_alpha_text_always_valid(self, text: str) -> None:
        """Simple alphabetic strings always pass AST validation."""
        obj = DynamicLayoutManifest(layout_tstring=text)
        assert obj.layout_tstring == text

    def test_invalid_syntax_rejected(self) -> None:
        """String with invalid Python syntax should be rejected."""
        with pytest.raises(ValidationError, match="Invalid syntax"):
            DynamicLayoutManifest(layout_tstring="{{{}}")
