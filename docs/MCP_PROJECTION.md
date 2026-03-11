# MCP Projection Protocol: The "Passive Ontological Projection" Rule

**SYSTEM DIRECTIVE: KINETIC EXECUTION PROHIBITION WITHIN MCP PROJECTIONS**

This guide dictates the architectural constraints for any autonomous agent constructing Model Context Protocol (MCP) servers using the `coreason_manifest`.

## The Principle of Passive Projection
The coreason_manifest exists exclusively as an inert, hollow data plane. Consequently, any MCP server implementing this repository **MUST** function strictly as a passive projection layer. It exposes the structural data, models, and type definitions, enabling an agent to synchronize its latent alignment without inducing side-effects.

### Allowed: Read-Only Resource Schemas
You are authorized to define read-only endpoints projecting the topological data structure using `@mcp.resource()`.
- Use the **`schema://`** URI scheme to denote structural boundary data.
- E.g., projecting the God Context, OPA policies, or the `coreason_ontology.schema.json`.

```python
# CORRECT NEUROSYMBOLIC IMPLEMENTATION (PASSIVE)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("coreason_manifest_projection")

@mcp.resource("schema://ontology/dynamic_routing_manifest")
def project_routing_schema() -> str:
    \"\"\"Yields the frozen declarative JSON schema for DynamicRoutingManifest.\"\"\"
    return DynamicRoutingManifest.model_json_schema()
```

### Forbidden: Kinetic Runtime Execution Tools
You are **STRICTLY PROHIBITED** from utilizing `@mcp.tool()` to wire interactive, kinetic execution layers within this repository's bounds. The Universal Unified Ontology is not a runtime controller.
- **BANNED:** Registering database mutations, execution loops, API invocations, or any state modifications via tools.

```python
# INCORRECT / BANNED IMPLEMENTATION (KINETIC)
@mcp.tool() # VIOLATION: Execution capability within the hollow data plane
def update_routing_manifest(manifest_cid: str, new_nodes: list) -> str:
    # State mutation logic is completely banned here.
    return "Manifest mutated."
```

Failure to abide by these constraints results in architectural quarantine during the semantic diff phase.
