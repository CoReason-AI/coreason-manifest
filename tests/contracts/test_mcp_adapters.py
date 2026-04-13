from coreason_manifest.spec.mcp import MCPToolDefinition
from coreason_manifest.utils.mcp_adapters import (
    generate_clingo_mcp_tool,
    generate_lean4_mcp_tool,
    generate_prolog_mcp_tool,
)


def test_generate_lean4_mcp_tool() -> None:
    tool = generate_lean4_mcp_tool()
    assert isinstance(tool, MCPToolDefinition)
    assert tool.name == "verify_lean4_theorem"
    assert "formal_statement" in tool.input_schema["properties"]
    assert "tactic_proof" in tool.input_schema["properties"]
    assert tool.input_schema["properties"]["formal_statement"]["maxLength"] == 100000
    assert tool.input_schema["properties"]["tactic_proof"]["maxLength"] == 100000
    assert tool.input_schema["required"] == ["formal_statement", "tactic_proof"]
    dump = tool.model_dump(by_alias=True)
    assert "inputSchema" in dump


def test_generate_clingo_mcp_tool() -> None:
    tool = generate_clingo_mcp_tool()
    assert isinstance(tool, MCPToolDefinition)
    assert tool.name == "execute_clingo_falsification"
    assert "asp_program" in tool.input_schema["properties"]
    assert "max_models" in tool.input_schema["properties"]
    assert tool.input_schema["properties"]["asp_program"]["maxLength"] == 65536
    assert tool.input_schema["properties"]["max_models"]["default"] == 1
    assert tool.input_schema["required"] == ["asp_program"]
    dump = tool.model_dump(by_alias=True)
    assert "inputSchema" in dump


def test_generate_prolog_mcp_tool() -> None:
    tool = generate_prolog_mcp_tool()
    assert isinstance(tool, MCPToolDefinition)
    assert tool.name == "execute_prolog_deduction"
    assert "prolog_query" in tool.input_schema["properties"]
    assert "ephemeral_facts" in tool.input_schema["properties"]
    assert tool.input_schema["required"] == ["prolog_query"]
    dump = tool.model_dump(by_alias=True)
    assert "inputSchema" in dump
