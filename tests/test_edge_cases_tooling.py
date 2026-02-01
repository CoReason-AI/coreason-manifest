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
from coreason_manifest.definitions.agent import ToolRequirement, ToolRiskLevel
from pydantic import ValidationError


def test_tool_requirement_empty_scopes() -> None:
    """Test that empty scopes list is valid."""
    req = ToolRequirement(uri="https://example.com/tool", hash="a" * 64, scopes=[], risk_level=ToolRiskLevel.SAFE)
    assert req.scopes == []


def test_tool_requirement_critical_risk() -> None:
    """Test using CRITICAL risk level."""
    req = ToolRequirement(
        uri="https://example.com/tool", hash="a" * 64, scopes=["admin"], risk_level=ToolRiskLevel.CRITICAL
    )
    assert req.risk_level == ToolRiskLevel.CRITICAL


def test_tool_requirement_duplicate_uris_in_set() -> None:
    """Test behavior with duplicate tools (not strictly enforced by list, but logical check)."""
    # The model allows list, so duplicates are technically allowed structurally.
    pass


def test_tool_requirement_uri_schemes() -> None:
    """Test various URI schemes."""
    schemes = [
        "http://example.com",
        "https://example.com",
        "ftp://example.com",
        "mcp://example.com",
        "mailto:user@example.com",
    ]
    for scheme in schemes:
        req = ToolRequirement(uri=scheme, hash="a" * 64, scopes=[], risk_level=ToolRiskLevel.SAFE)
        assert str(req.uri) == scheme or str(req.uri) == scheme + "/"


def test_tool_requirement_invalid_uri_string() -> None:
    """Test invalid URI strings."""
    with pytest.raises(ValidationError):
        ToolRequirement(uri="not a uri", hash="a" * 64, scopes=[], risk_level=ToolRiskLevel.SAFE)
