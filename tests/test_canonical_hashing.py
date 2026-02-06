import json
import hashlib
import pytest
from coreason_manifest.spec.v2.definitions import ToolDefinition
from coreason_manifest.spec.common_base import ToolRiskLevel, CoReasonBaseModel

class TestCanonicalHashing:
    def test_determinism(self) -> None:
        """Test that two identical models produce the same hash."""
        tool1 = ToolDefinition(
            id="tool-1",
            name="My Tool",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="A test tool"
        )
        tool2 = ToolDefinition(
            id="tool-1",
            name="My Tool",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="A test tool"
        )
        assert tool1.compute_hash() == tool2.compute_hash()

    def test_sensitivity(self) -> None:
        """Test that changing one field changes the hash."""
        tool1 = ToolDefinition(
            id="tool-1",
            name="My Tool",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="A test tool"
        )
        tool2 = ToolDefinition(
            id="tool-1",
            name="My Tool Changed",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="A test tool"
        )
        assert tool1.compute_hash() != tool2.compute_hash()

    def test_exclusion(self) -> None:
        """Test that excluded fields do not affect the hash."""
        tool1 = ToolDefinition(
            id="tool-1",
            name="My Tool",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="A test tool"
        )
        tool2 = ToolDefinition(
            id="tool-1",
            name="My Tool",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="Different description"
        )

        # Hashes should differ normally
        assert tool1.compute_hash() != tool2.compute_hash()

        # Hashes should be same when description is excluded
        assert tool1.compute_hash(exclude={"description"}) == tool2.compute_hash(exclude={"description"})

    def test_canonicalization_order(self) -> None:
        """Test that key order does not affect the hash."""
        tool = ToolDefinition(
            id="tool-1",
            name="My Tool",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="A test tool"
        )

        hash1 = tool.compute_hash()

        data = tool.dump()
        # Create a new dict with reversed keys
        reversed_data = {k: data[k] for k in reversed(list(data.keys()))}

        # Verify that if we manually hash the reversed dict with sort_keys=True, it matches
        json_str = json.dumps(reversed_data, sort_keys=True, ensure_ascii=False)
        expected_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

        assert hash1 == expected_hash

    def test_unicode_support(self) -> None:
        """Test that unicode characters are handled correctly."""
        tool = ToolDefinition(
            id="tool-unicode",
            name="My Tool 🚀",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="Test with unicode: \u00e9"
        )

        # Should not raise
        h = tool.compute_hash()
        assert isinstance(h, str)
        assert len(h) == 64

        # Deterministic check
        tool2 = ToolDefinition(
            id="tool-unicode",
            name="My Tool 🚀",
            uri="https://example.com/tool",
            risk_level=ToolRiskLevel.SAFE,
            description="Test with unicode: \u00e9"
        )
        assert h == tool2.compute_hash()
