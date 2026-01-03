# Prosperity-3.0
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.models import AgentMetadata


def test_semver_build_metadata() -> None:
    """Test SemVer with build metadata."""
    metadata = AgentMetadata(
        id=uuid4(),
        version="1.0.0+build.123",
        name="Test",
        author="Me",
        created_at="2023-01-01T00:00:00Z"
    )
    assert metadata.version == "1.0.0+build.123"


def test_semver_prerelease() -> None:
    """Test SemVer with pre-release tags."""
    metadata = AgentMetadata(
        id=uuid4(),
        version="1.0.0-alpha.1",
        name="Test",
        author="Me",
        created_at="2023-01-01T00:00:00Z"
    )
    assert metadata.version == "1.0.0-alpha.1"


def test_semver_invalid_short() -> None:
    """Test invalid SemVer (too short)."""
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0",
            name="Test",
            author="Me",
            created_at="2023-01-01T00:00:00Z"
        )
    assert "not a valid SemVer string" in str(e.value)


def test_semver_invalid_prefix() -> None:
    """Test invalid SemVer (prefix)."""
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="v1.0.0",
            name="Test",
            author="Me",
            created_at="2023-01-01T00:00:00Z"
        )
    assert "not a valid SemVer string" in str(e.value)


def test_semver_invalid_quad() -> None:
    """Test invalid SemVer (four parts)."""
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0.0.0",
            name="Test",
            author="Me",
            created_at="2023-01-01T00:00:00Z"
        )
    assert "not a valid SemVer string" in str(e.value)
