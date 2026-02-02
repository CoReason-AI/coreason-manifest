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

from coreason_manifest.definitions.presentation import (
    DataBlock,
    MarkdownBlock,
    PresentationBlockType,
    ThinkingBlock,
    UserErrorBlock,
)


def test_thinking_block_serialization() -> None:
    """Test serialization of ThinkingBlock."""
    block = ThinkingBlock(content="Thinking about the problem...")
    dumped = block.dump()
    assert dumped["block_type"] == "THOUGHT"
    assert dumped["content"] == "Thinking about the problem..."
    assert dumped["status"] == "IN_PROGRESS"
    assert isinstance(dumped["id"], str)

    json_str = block.to_json()
    # Check for presence of key fields in JSON
    assert '"block_type":"THOUGHT"' in json_str or '"block_type": "THOUGHT"' in json_str


def test_data_block_structure() -> None:
    """Test DataBlock structure preservation."""
    data = {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
    block = DataBlock(data=data, view_hint="TABLE", title="User List")
    dumped = block.dump()

    assert dumped["block_type"] == "DATA"
    assert dumped["data"] == data
    assert dumped["view_hint"] == "TABLE"
    assert dumped["title"] == "User List"


def test_data_block_validation() -> None:
    """Test validation of DataBlock fields."""
    # Test invalid view_hint
    with pytest.raises(ValidationError):
        DataBlock(data={}, view_hint="SCATTER_PLOT")  # type: ignore


def test_markdown_block() -> None:
    """Test MarkdownBlock."""
    content = "# Heading\n\n- Item 1\n- Item 2"
    block = MarkdownBlock(content=content)
    dumped = block.dump()
    assert dumped["block_type"] == "MARKDOWN"
    assert dumped["content"] == content


def test_user_error_block() -> None:
    """Test UserErrorBlock."""
    block = UserErrorBlock(
        user_message="Something went wrong",
        technical_details={"code": 500},
        recoverable=True
    )
    dumped = block.dump()
    assert dumped["block_type"] == "ERROR"
    assert dumped["user_message"] == "Something went wrong"
    assert dumped["technical_details"] == {"code": 500}
    assert dumped["recoverable"] is True


def test_inheritance() -> None:
    """Verify inheritance from CoReasonBaseModel."""
    from coreason_manifest.definitions.base import CoReasonBaseModel
    assert issubclass(ThinkingBlock, CoReasonBaseModel)
    assert issubclass(DataBlock, CoReasonBaseModel)
