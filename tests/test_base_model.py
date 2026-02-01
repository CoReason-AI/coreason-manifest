# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from datetime import datetime

from coreason_manifest.definitions.base import CoReasonBaseModel
from pydantic import Field


class TestModel(CoReasonBaseModel):
    """Test model for verifying CoReasonBaseModel functionality."""

    id: str = "123"
    dt: datetime = Field(default_factory=datetime.now)
    optional: str | None = None


def test_dump_serialization() -> None:
    """Test dump() serialization."""
    m = TestModel()
    dumped = m.dump()
    assert isinstance(dumped["dt"], str)
    assert dumped["id"] == "123"
    assert "optional" not in dumped  # exclude_none=True default


def test_dump_overrides() -> None:
    """Test dump() with overrides."""
    m = TestModel()
    # Override exclude_none
    dumped = m.dump(exclude_none=False)
    assert dumped["optional"] is None


def test_to_json_serialization() -> None:
    """Test to_json() serialization."""
    m = TestModel()
    json_str = m.to_json()
    assert isinstance(json_str, str)
    loaded = json.loads(json_str)
    assert loaded["id"] == "123"


def test_to_json_overrides() -> None:
    """Test to_json() with overrides."""
    m = TestModel()
    json_str = m.to_json(exclude_none=False)
    loaded = json.loads(json_str)
    assert loaded["optional"] is None
