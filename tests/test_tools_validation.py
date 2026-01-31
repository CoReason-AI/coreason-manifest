# Prosperity-3.0
import pytest
from pydantic import AnyUrl, TypeAdapter, ValidationError

from coreason_manifest.definitions.agent import AgentDependencies

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
    # Check that they are stored as AnyUrl (StrictUri is AnyUrl at runtime until serialized)
    assert len(deps.tools) == 5
    assert str(deps.tools[0]) == "https://example.com/tool"
    assert str(deps.tools[2]) == "mcp://server/capability"
    assert isinstance(deps.tools[0], AnyUrl)


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
        # "https://" can be valid depending on strictness, skipping strict check here
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

    # model_dump() in python mode returns strings now due to PlainSerializer
    dumped = deps.model_dump()
    assert isinstance(dumped["tools"][0], str)
    assert dumped["tools"][0] == "https://example.com/"

    # Check JSON dump (should be strings)
    json_dump = deps.model_dump_json()
    assert '"https://example.com/"' in json_dump
