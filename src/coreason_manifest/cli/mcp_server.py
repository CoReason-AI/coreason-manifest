# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import asyncio
import contextlib
from typing import Any, cast

from mcp.server.fastmcp import FastMCP
from pydantic import TypeAdapter

import coreason_manifest
from coreason_manifest.cli.transport import secure_stdio_server
from coreason_manifest.core import CoreasonBaseModel

# Create an MCP server
mcp = FastMCP("coreason-manifest-schema-service")

_AVAILABLE_SCHEMAS: dict[str, Any] = {}

for _name in coreason_manifest.__all__:
    _obj = getattr(coreason_manifest, _name, None)
    # Skip None and the abstract base class itself
    if _obj is None or _obj is CoreasonBaseModel:
        continue

    with contextlib.suppress(Exception):
        _AVAILABLE_SCHEMAS[_name] = TypeAdapter(_obj).json_schema()

_SCHEMA_NAMES = sorted(_AVAILABLE_SCHEMAS.keys())


@mcp.tool()
def list_schemas() -> list[str]:
    """Returns a list of all available schema names exported in the root __init__.py."""
    return _SCHEMA_NAMES


@mcp.tool()
def get_schema(schema_name: str) -> dict[str, Any]:
    """Returns the strict Pydantic JSON schema for a specific requested model.

    Args:
        schema_name: The name of the schema to fetch (e.g., WorkingMemorySnapshot)
    """
    if schema_name not in _AVAILABLE_SCHEMAS:
        raise ValueError(f"Schema '{schema_name}' not found in the manifest.")

    return cast("dict[str, Any]", _AVAILABLE_SCHEMAS[schema_name])


async def _run_server() -> None:
    # We dynamically extract the inner Server from FastMCP to bypass its default stdio transport
    server = mcp._mcp_server

    async with secure_stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:  # pragma: no cover
    """Main entrypoint for the secure MCP Server."""
    asyncio.run(_run_server())


if __name__ == "__main__":
    main()
