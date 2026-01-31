import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import ToolRequirement, ToolRiskLevel


def test_tool_requirement_valid() -> None:
    """Test creating a valid ToolRequirement."""
    req = ToolRequirement(
        uri="https://example.com/tool", hash="a" * 64, scopes=["read", "write"], risk_level=ToolRiskLevel.SAFE
    )
    assert str(req.uri) == "https://example.com/tool"
    assert req.hash == "a" * 64
    assert req.scopes == ["read", "write"]
    assert req.risk_level == ToolRiskLevel.SAFE


def test_tool_requirement_invalid_hash() -> None:
    """Test that invalid hash raises ValidationError."""
    with pytest.raises(ValidationError):
        ToolRequirement(uri="https://example.com/tool", hash="invalid", scopes=[], risk_level=ToolRiskLevel.SAFE)


def test_tool_requirement_invalid_risk_level() -> None:
    """Test that invalid risk level raises ValidationError."""
    with pytest.raises(ValidationError):
        ToolRequirement(
            uri="https://example.com/tool",
            hash="a" * 64,
            scopes=[],
            risk_level="unknown",  # type: ignore
        )


def test_tool_requirement_invalid_uri() -> None:
    """Test that invalid URI raises ValidationError."""
    with pytest.raises(ValidationError):
        ToolRequirement(uri="not-a-uri", hash="a" * 64, scopes=[], risk_level=ToolRiskLevel.SAFE)


def test_tool_requirement_serialization() -> None:
    """Test that ToolRequirement can be serialized."""
    req = ToolRequirement(
        uri="https://example.com/tool", hash="a" * 64, scopes=["read"], risk_level=ToolRiskLevel.CRITICAL
    )
    dumped = req.model_dump()
    assert dumped["uri"] == "https://example.com/tool"
    assert dumped["risk_level"] == "critical"
