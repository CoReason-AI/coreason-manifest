from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from pydantic import AnyUrl, ValidationError

from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import AgentDependencies


@pytest.fixture
def raw_agent_dict() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "Test",
            "author": "Test",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"steps": [], "model_config": {"model": "gpt-4", "temperature": 0.1}},
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "a" * 64,
    }


def create_temp_manifest(tmp_path: Path, data: Dict[str, Any]) -> Path:
    p = tmp_path / "agent.yaml"
    with open(p, "w") as f:
        yaml.dump(data, f)
    return p


# --- SemVer Normalization Edge Cases ---


def test_normalization_complex_versions(tmp_path: Path, raw_agent_dict: Dict[str, Any]) -> None:
    """Test normalization with complex SemVer strings."""
    cases = [
        ("v1.0.0-alpha", "1.0.0-alpha"),
        ("V1.0.0+build.123", "1.0.0+build.123"),
        ("v1.0.0-beta+exp.sha.5114f85", "1.0.0-beta+exp.sha.5114f85"),
        ("1.2.3", "1.2.3"),  # Already normalized
    ]

    for input_ver, expected_ver in cases:
        raw_agent_dict["metadata"]["version"] = input_ver
        p = create_temp_manifest(tmp_path, raw_agent_dict)
        data = ManifestLoader.load_raw_from_file(p)
        assert data["metadata"]["version"] == expected_ver, f"Failed for {input_ver} in raw load"

        agent = ManifestLoader.load_from_file(p)
        assert agent.metadata.version == expected_ver, f"Failed for {input_ver} in model load"

    # Edge Case: Double 'v'
    # load_raw strips one 'v' -> 'v1.0.0'
    # load_from_file (model) strips second 'v' -> '1.0.0'
    raw_agent_dict["metadata"]["version"] = "vv1.0.0"
    p = create_temp_manifest(tmp_path, raw_agent_dict)

    raw_data = ManifestLoader.load_raw_from_file(p)
    assert raw_data["metadata"]["version"] == "v1.0.0"

    agent = ManifestLoader.load_from_file(p)
    assert agent.metadata.version == "1.0.0"

    # Edge Case: Triple 'v' -> Passes due to recursive normalization
    raw_agent_dict["metadata"]["version"] = "vvv1.0.0"
    p = create_temp_manifest(tmp_path, raw_agent_dict)
    agent = ManifestLoader.load_from_file(p)
    assert agent.metadata.version == "1.0.0"

    # Edge Case: Quadruple 'v' -> Should pass now due to recursive normalization and lenient regex
    raw_agent_dict["metadata"]["version"] = "vvvv1.0.0"
    p = create_temp_manifest(tmp_path, raw_agent_dict)

    # It should pass now
    agent = ManifestLoader.load_from_file(p)
    assert agent.metadata.version == "1.0.0"


def test_normalization_missing_fields(tmp_path: Path, raw_agent_dict: Dict[str, Any]) -> None:
    """Test normalization is robust against missing fields."""
    # Case 1: No version
    del raw_agent_dict["metadata"]["version"]
    p = create_temp_manifest(tmp_path, raw_agent_dict)
    data = ManifestLoader.load_raw_from_file(p)
    assert "version" not in data["metadata"]  # Should remain missing

    # Case 2: No metadata
    del raw_agent_dict["metadata"]
    p = create_temp_manifest(tmp_path, raw_agent_dict)
    data = ManifestLoader.load_raw_from_file(p)
    assert "metadata" not in data  # Should remain missing


def test_normalization_non_string_version(tmp_path: Path, raw_agent_dict: Dict[str, Any]) -> None:
    """Test normalization ignores non-string versions."""
    raw_agent_dict["metadata"]["version"] = 1.0  # Float
    p = create_temp_manifest(tmp_path, raw_agent_dict)
    data = ManifestLoader.load_raw_from_file(p)
    assert data["metadata"]["version"] == 1.0  # Unchanged


def test_normalization_false_positives(tmp_path: Path, raw_agent_dict: Dict[str, Any]) -> None:
    """Test stripping 'v' from non-semver strings."""
    # The current logic blindly strips leading 'v'.
    # This test documents that behavior. The subsequent Schema validation will catch invalid versions.
    raw_agent_dict["metadata"]["version"] = "very-bad-version"
    p = create_temp_manifest(tmp_path, raw_agent_dict)
    data = ManifestLoader.load_raw_from_file(p)
    assert data["metadata"]["version"] == "ery-bad-version"


def test_normalization_direct_dict_load(raw_agent_dict: Dict[str, Any]) -> None:
    """Verify load_from_dict performs normalization."""
    raw_agent_dict["metadata"]["version"] = "v2.0.0"
    agent = ManifestLoader.load_from_dict(raw_agent_dict)
    assert agent.metadata.version == "2.0.0"


# --- URI Validation Edge Cases ---


def test_uri_validation_edge_cases() -> None:
    """Test strict URI validation edge cases."""

    # Unicode in domain (IDNA)
    unicode_uri = "https://münchen.de"
    try:
        deps = AgentDependencies(tools=[unicode_uri])
        # Check normalization if it passes
        assert str(deps.tools[0]) in ["https://münchen.de/", "https://xn--mnchen-3ya.de/"]
    except ValidationError:
        pass

    # Invalid Port
    with pytest.raises(ValidationError, match="Input should be a valid URL"):
        AgentDependencies(tools=["http://example.com:999999"])

    # Missing Host with http scheme (strict)
    with pytest.raises(ValidationError):
        AgentDependencies(tools=["http://"])

    # Spaces in URI - Pydantic AnyUrl often encodes them
    deps = AgentDependencies(tools=["http://example.com/foo bar"])
    assert "%20" in str(deps.tools[0]) or " " in str(deps.tools[0])

    # Definitely invalid URI (Non-numeric port)
    with pytest.raises(ValidationError):
        AgentDependencies(tools=["http://example.com:abc"])

    # Test mcp:// (custom scheme) is accepted as a URL structure
    deps = AgentDependencies(tools=["mcp://"])
    assert str(deps.tools[0]) in ["mcp://", "mcp:///"]

    # Test list mutability
    deps = AgentDependencies(tools=["http://example.com"])
    assert len(deps.tools) == 1
    deps.tools.append(AnyUrl("http://example.org"))  # Should succeed and satisfy Mypy
    assert len(deps.tools) == 2
    assert str(deps.tools[1]) in ["http://example.org/", "http://example.org"]
