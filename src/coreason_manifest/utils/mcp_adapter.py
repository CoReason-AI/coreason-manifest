from coreason_manifest.spec.core.contracts import AtomicSkill, StrictJsonValue


def compile_skill_to_mcp(skill: AtomicSkill, server_uri: str) -> dict[str, StrictJsonValue]:
    """
    Compiles a strictly-typed AtomicSkill into an outbound MCP JSON-RPC payload.
    """
    # Cast to circumvent the recursive bounds during dict construction
    return {
        "name": skill.name,
        "inputSchema": skill.definition,
        "server_uri": server_uri,
    }
