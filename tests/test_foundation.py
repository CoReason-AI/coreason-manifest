# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from uuid import UUID, uuid4

from coreason_manifest.spec.common_base import ManifestBaseModel, StrictUri, ToolRiskLevel


class FoundationTestModel(ManifestBaseModel):
    id: UUID
    timestamp: datetime
    uri: StrictUri
    risk: ToolRiskLevel


def test_foundation_serialization() -> None:
    """Test that ManifestBaseModel.model_dump(...) serializes complex types to strings."""
    model = FoundationTestModel(
        id=uuid4(),
        timestamp=datetime.now(UTC),
        uri="https://example.com",
        risk=ToolRiskLevel.SAFE,
    )

    data = model.model_dump(mode="json", by_alias=True, exclude_none=True)

    # Verify UUID is serialized to str
    assert isinstance(data["id"], str)

    # Verify datetime is serialized to str (ISO format)
    assert isinstance(data["timestamp"], str)

    # Verify StrictUri is serialized to str
    assert isinstance(data["uri"], str)
    assert data["uri"] == "https://example.com/"  # AnyUrl adds trailing slash or normalizes

    # Verify Enum is serialized to str
    assert isinstance(data["risk"], str)
    assert data["risk"] == "safe"


def test_foundation_json() -> None:
    """Test that ManifestBaseModel.model_dump_json(by_alias=True, exclude_none=True) produces valid JSON string."""
    model = FoundationTestModel(
        id=uuid4(),
        timestamp=datetime.now(UTC),
        uri="https://example.com",
        risk=ToolRiskLevel.SAFE,
    )

    json_str = model.model_dump_json(by_alias=True, exclude_none=True)

    assert isinstance(json_str, str)
    assert str(model.id) in json_str
    assert "https://example.com" in json_str
    assert "safe" in json_str
