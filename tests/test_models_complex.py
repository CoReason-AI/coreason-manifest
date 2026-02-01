# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import AgentMetadata


def test_semver_build_metadata() -> None:
    """Test SemVer with build metadata."""
    metadata = AgentMetadata(
        id=uuid4(), version="1.0.0+build.123", name="Test", author="Me", created_at="2023-01-01T00:00:00Z"
    )
    assert metadata.version == "1.0.0+build.123"


def test_semver_prerelease() -> None:
    """Test SemVer with pre-release tags."""
    metadata = AgentMetadata(
        id=uuid4(), version="1.0.0-alpha.1", name="Test", author="Me", created_at="2023-01-01T00:00:00Z"
    )
    assert metadata.version == "1.0.0-alpha.1"


def test_semver_invalid_short() -> None:
    """Test invalid SemVer (too short)."""
    with pytest.raises(ValidationError) as e:
        AgentMetadata(id=uuid4(), version="1.0", name="Test", author="Me", created_at="2023-01-01T00:00:00Z")
    assert "String should match pattern" in str(e.value)


def test_semver_valid_prefix_normalized() -> None:
    """Test that SemVer with 'v' prefix is now valid and normalized."""
    metadata = AgentMetadata(id=uuid4(), version="v1.0.0", name="Test", author="Me", created_at="2023-01-01T00:00:00Z")
    assert metadata.version == "1.0.0"


def test_semver_invalid_quad() -> None:
    """Test invalid SemVer (four parts)."""
    with pytest.raises(ValidationError) as e:
        AgentMetadata(id=uuid4(), version="1.0.0.0", name="Test", author="Me", created_at="2023-01-01T00:00:00Z")
    assert "String should match pattern" in str(e.value)
