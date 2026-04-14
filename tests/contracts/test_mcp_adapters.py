from coreason_manifest.spec.ontology import (
    MCPToolDefinition,
    generate_clingo_mcp_tool,
    generate_lean4_mcp_tool,
    generate_prolog_mcp_tool,
)


def test_generate_lean4_mcp_tool() -> None:
    tool = generate_lean4_mcp_tool()
    assert isinstance(tool, MCPToolDefinition)
    assert tool.name == "verify_lean4_theorem"
    props = tool.input_schema["properties"]
    assert isinstance(props, dict)
    assert "formal_statement" in props
    assert "tactic_proof" in props

    formal_statement = props["formal_statement"]
    assert isinstance(formal_statement, dict)
    assert formal_statement["maxLength"] == 100000

    tactic_proof = props["tactic_proof"]
    assert isinstance(tactic_proof, dict)
    assert tactic_proof["maxLength"] == 100000

    assert tool.input_schema["required"] == ["formal_statement", "tactic_proof"]
    dump = tool.model_dump(by_alias=True)
    assert "inputSchema" in dump


def test_generate_clingo_mcp_tool() -> None:
    tool = generate_clingo_mcp_tool()
    assert isinstance(tool, MCPToolDefinition)
    assert tool.name == "execute_clingo_falsification"
    props = tool.input_schema["properties"]
    assert isinstance(props, dict)
    assert "asp_program" in props
    assert "max_models" in props

    asp_program = props["asp_program"]
    assert isinstance(asp_program, dict)
    assert asp_program["maxLength"] == 65536

    max_models = props["max_models"]
    assert isinstance(max_models, dict)
    assert max_models["default"] == 1

    assert tool.input_schema["required"] == ["asp_program"]
    dump = tool.model_dump(by_alias=True)
    assert "inputSchema" in dump


def test_generate_prolog_mcp_tool() -> None:
    tool = generate_prolog_mcp_tool()
    assert isinstance(tool, MCPToolDefinition)
    assert tool.name == "execute_prolog_deduction"
    props = tool.input_schema["properties"]
    assert isinstance(props, dict)
    assert "prolog_query" in props
    assert "ephemeral_facts" in props

    assert tool.input_schema["required"] == ["prolog_query"]
    dump = tool.model_dump(by_alias=True)
    assert "inputSchema" in dump
