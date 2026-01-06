# Prosperity-3.0
import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.models import AgentDependencies

# Create a TypeAdapter for easy testing of the tuple field
ToolsAdapter = TypeAdapter(AgentDependencies)


def test_tools_validation_valid_uris() -> None:
    """Test valid URIs are accepted."""
    valid_uris = [
        "https://example.com/tool",
        "http://localhost:8080/mcp",
        "mcp://server/capability",
        "mcp+ssh://user@host/path",
        "ftp://files.example.com",
    ]
    deps = AgentDependencies(tools=tuple(valid_uris))
    # Check that they are stored as AnyUrl (or compatible)
    assert len(deps.tools) == 5
    assert str(deps.tools[0]) == "https://example.com/tool"
    assert str(deps.tools[2]) == "mcp://server/capability"


def test_tools_validation_complex_cases() -> None:
    """Test complex but valid URIs."""
    complex_uris = [
        "https://user:pass@example.com:8443/path/to/resource?query=param&key=value#fragment",
        "mcp://192.168.1.1:5000/cap",
        "http://[2001:db8::1]/index.html",  # IPv6
        "custom.scheme://resource",
    ]
    deps = AgentDependencies(tools=tuple(complex_uris))
    assert len(deps.tools) == 4
    assert deps.tools[0].port == 8443
    assert deps.tools[0].username == "user"


def test_tools_validation_invalid_uris() -> None:
    """Test invalid URIs are rejected."""
    invalid_uris = [
        "not-a-uri",
        "missing-scheme.com",
        "http:// example.com",  # Space
        "://missing-scheme",
        "https://",  # Empty host (allowed by some parsers, but AnyUrl usually requires host depending on strictness)
    ]

    # Test one by one to ensure each fails
    for uri in invalid_uris:
        with pytest.raises(ValidationError, match="Input should be a valid URL"):
            AgentDependencies(tools=(uri,))


def test_tools_validation_empty_list() -> None:
    """Test empty list is valid."""
    deps = AgentDependencies(tools=())
    assert len(deps.tools) == 0


def test_tools_serialization() -> None:
    """Test that tools are serialized to strings."""
    deps = AgentDependencies(tools=("https://example.com", "mcp://tool"))
    dumped = deps.model_dump()
    # Pydantic AnyUrl adds a trailing slash to http/https URLs with no path
    assert dumped["tools"] == ("https://example.com/", "mcp://tool")

    # Check JSON dump
    json_dump = deps.model_dump_json()
    assert '"https://example.com/"' in json_dump
