import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core import MCPPrompt, MCPResourceTemplate, MCPTool, ToolPack
from coreason_manifest.utils.mcp_adapter import pack_to_mcp_prompts, pack_to_mcp_resources, parse_mcp_tool_payload


def test_mcp_resource_template_success() -> None:
    tpl = MCPResourceTemplate(uri_template="mcp://file/{name}", name="file_reader", mime_type="text/plain")
    assert tpl.uri_template == "mcp://file/{name}"  # noqa: S101
    assert tpl.name == "file_reader"  # noqa: S101
    assert tpl.mime_type == "text/plain"  # noqa: S101


def test_mcp_prompt_success() -> None:
    prompt = MCPPrompt(name="analyze", description="Analyze code", arguments=[{"name": "code", "type": "string"}])
    assert prompt.name == "analyze"  # noqa: S101
    assert prompt.arguments is not None  # noqa: S101
    assert len(prompt.arguments) == 1  # noqa: S101


def test_mcp_tool_success() -> None:
    tool = MCPTool(
        name="github_mcp",
        server_uri="http://localhost:8080/mcp",  # type: ignore
        mcp_version="1.0.0",
        supported_capabilities=["resources", "prompts"],
        prompts=[MCPPrompt(name="review", arguments=[])],
        resource_templates=[MCPResourceTemplate(uri_template="mcp://repo/{id}", name="repo_reader")],
    )
    assert tool.type == "mcp_tool"  # noqa: S101
    assert tool.mcp_version == "1.0.0"  # noqa: S101
    assert len(tool.prompts) == 1  # noqa: S101
    assert len(tool.resource_templates) == 1  # noqa: S101


def test_mcp_tool_failure() -> None:
    # Invalid URI
    with pytest.raises(ValidationError):
        MCPTool(name="bad_tool", server_uri="not-a-url", mcp_version="1.0.0")  # type: ignore


def test_mcp_adapter_resources() -> None:
    pack = ToolPack(
        namespace="test",
        tools=[
            MCPTool(
                name="mcp1",
                server_uri="http://mcp.local",  # type: ignore
                mcp_version="1.0.0",
                resource_templates=[
                    MCPResourceTemplate(uri_template="mcp://docs/{id}", name="docs", mime_type="text/markdown")
                ],
            ),
            {"name": "standard_tool", "type": "capability"},  # type: ignore
        ],
    )

    resources = pack_to_mcp_resources(pack)
    assert len(resources) == 2  # noqa: S101

    # Verify MCP tool extraction
    assert resources[0]["uri"] == "mcp://docs/{id}"  # noqa: S101
    assert resources[0]["mimeType"] == "text/markdown"  # noqa: S101

    # Verify fallback standard tool
    assert resources[1]["uri"] == "mcp://test/standard_tool"  # noqa: S101


def test_mcp_adapter_prompts() -> None:
    pack = ToolPack(
        namespace="test",
        tools=[
            MCPTool(
                name="mcp1",
                server_uri="http://mcp.local",  # type: ignore
                mcp_version="1.0.0",
                prompts=[MCPPrompt(name="summarize", description="Summarize text", arguments=[{"text": "string"}])],
            )
        ],
    )

    prompts = pack_to_mcp_prompts(pack)
    assert len(prompts) == 1  # noqa: S101
    assert prompts[0]["name"] == "summarize"  # noqa: S101
    assert prompts[0]["description"] == "Summarize text"  # noqa: S101
    assert len(prompts[0]["arguments"]) == 1  # noqa: S101


def test_parse_mcp_tool_payload() -> None:
    tool = MCPTool(
        name="test_mcp",
        server_uri="http://mcp.local/api",  # type: ignore
        mcp_version="1.2.0",
        supported_capabilities=["logging"],
    )

    payload = parse_mcp_tool_payload(tool)
    assert payload["mcp_version"] == "1.2.0"  # noqa: S101
    assert payload["capabilities"] == ["logging"]  # noqa: S101
    assert "http://mcp.local/api" in payload["server_uri"]  # noqa: S101
