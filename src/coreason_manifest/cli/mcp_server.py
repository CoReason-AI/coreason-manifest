from typing import Any

from mcp.server.fastmcp import FastMCP

import coreason_manifest

# Create an MCP server
mcp = FastMCP("coreason-manifest-schema-service")


@mcp.tool()
def list_schemas() -> list[str]:
    """Returns a list of all available schema names exported in the root __init__.py."""
    schemas = []

    # Check if the model is exported and is a CoreasonBaseModel
    from coreason_manifest.core import CoreasonBaseModel

    for name in getattr(coreason_manifest, "__all__", []):
        obj = getattr(coreason_manifest, name)
        if isinstance(obj, type) and issubclass(obj, CoreasonBaseModel) and obj is not CoreasonBaseModel:
            schemas.append(name)

    return sorted(schemas)


@mcp.tool()
def get_schema(schema_name: str) -> dict[str, Any]:
    """Returns the strict Pydantic JSON schema for a specific requested model.

    Args:
        schema_name: The name of the schema to fetch (e.g., WorkingMemorySnapshot)
    """
    from coreason_manifest.core import CoreasonBaseModel

    if schema_name not in getattr(coreason_manifest, "__all__", []):
        raise ValueError(f"Schema '{schema_name}' not found in the manifest.")

    obj = getattr(coreason_manifest, schema_name)
    if not isinstance(obj, type) or not issubclass(obj, CoreasonBaseModel):
        raise ValueError(f"'{schema_name}' is not a valid schema model.")

    # Generate JSON schema using Pydantic
    return obj.model_json_schema()


def main() -> None:
    """Main entrypoint for the MCP Server using stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
