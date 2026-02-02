# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.session import Interaction, LineageMetadata


def test_lineage_metadata_creation() -> None:
    """Test successful creation of LineageMetadata."""
    lineage = LineageMetadata(
        root_request_id="req-123",
        parent_interaction_id="int-456",
    )
    assert lineage.root_request_id == "req-123"
    assert lineage.parent_interaction_id == "int-456"


def test_lineage_metadata_optional_fields() -> None:
    """Test LineageMetadata optional fields."""
    lineage = LineageMetadata()
    assert lineage.root_request_id is None
    assert lineage.parent_interaction_id is None


def test_lineage_metadata_immutability() -> None:
    """Test that LineageMetadata is immutable."""
    lineage = LineageMetadata(root_request_id="req-1")
    with pytest.raises(ValidationError):
        lineage.root_request_id = "req-2"  # type: ignore


def test_interaction_with_lineage() -> None:
    """Test Interaction with lineage metadata."""
    lineage = LineageMetadata(root_request_id="root-1", parent_interaction_id="parent-1")
    interaction = Interaction(
        input={"content": "hello"},
        output={"content": "world"},
        lineage=lineage,
    )
    assert interaction.lineage is not None
    assert interaction.lineage.root_request_id == "root-1"
    assert interaction.lineage.parent_interaction_id == "parent-1"


def test_interaction_default_lineage() -> None:
    """Test Interaction default lineage is None (backward compatibility)."""
    interaction = Interaction(
        input={"content": "hello"},
        output={"content": "world"},
    )
    assert interaction.lineage is None
