from coreason_manifest.spec.ontology import MCPToolDefinition


def generate_lean4_mcp_tool() -> MCPToolDefinition:
    return MCPToolDefinition(
        name="verify_lean4_theorem",
        description="Use this tool to evaluate constructive mathematical proofs and universal invariants in Lean 4. Returns the verification status or the failing tactic state.",
        input_schema={
            "type": "object",
            "properties": {
                "formal_statement": {"type": "string", "maxLength": 100000},
                "tactic_proof": {"type": "string", "maxLength": 100000},
            },
            "required": ["formal_statement", "tactic_proof"],
        },
    )


def generate_clingo_mcp_tool() -> MCPToolDefinition:
    return MCPToolDefinition(
        name="execute_clingo_falsification",
        description="Use this tool to hunt for counter-models and evaluate NP-hard constraint satisfaction problems using Answer Set Programming (ASP).",
        input_schema={
            "type": "object",
            "properties": {
                "asp_program": {"type": "string", "maxLength": 65536},
                "max_models": {"type": "integer", "default": 1},
            },
            "required": ["asp_program"],
        },
    )


def generate_prolog_mcp_tool() -> MCPToolDefinition:
    return MCPToolDefinition(
        name="execute_prolog_deduction",
        description="Use this tool for evidentiary grounding, exact subgraph isomorphism, and traversing hierarchical knowledge bases via backward-chaining resolution.",
        input_schema={
            "type": "object",
            "properties": {"prolog_query": {"type": "string"}, "ephemeral_facts": {"type": "string"}},
            "required": ["prolog_query"],
        },
    )
