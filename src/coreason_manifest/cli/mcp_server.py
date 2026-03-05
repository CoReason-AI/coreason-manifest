# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

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


def _global_error_handler_shield() -> None:
    """
    Patch the internal MCP server request handler to natively catch all exceptions,
    including validation errors, to guarantee the Poison Pill bounds are upheld
    and return strict JSON-RPC Error Envelopes.
    """
    import logging

    from mcp.server import Server
    from mcp.shared.session import BaseSession
    from pydantic import ValidationError

    from coreason_manifest.adapters.mcp.schemas import JSONRPCError, JSONRPCErrorResponse

    original_handle_message = Server._handle_message
    logger = logging.getLogger(__name__)

    async def _safe_handle_message(
        self,
        message: Any,
        session: BaseSession,
        lifespan_context: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        from coreason_manifest.adapters.mcp.schemas import BoundedJSONRPCRequest

        try:
            # When the stdio parser fails, FastMCP sends the raw Exception
            # Or if it succeeds, FastMCP parses it into a JSONRPCMessage and sends the wrapper `SessionMessage`
            if isinstance(message, Exception):
                raise message

            # Pre-validate the internal representation to ensure it adheres to boundary conditions
            # FastMCP `SessionMessage` encapsulates the incoming message
            if hasattr(message, "message") and hasattr(message.message, "model_dump"):
                raw_dict = message.message.model_dump(by_alias=True, exclude_none=True)
                BoundedJSONRPCRequest.model_validate(raw_dict)

            # Delegate to standard handler with correct signature arguments
            await original_handle_message(self, message, session, lifespan_context, *args, **kwargs)
        except ValidationError as ve:
            logger.error(f"MCP Schema Validation Error: {ve}")
            error_response = JSONRPCErrorResponse(
                jsonrpc="2.0",
                error=JSONRPCError(
                    code=-32600,
                    message="Invalid Request: Payload failed schema validation boundaries.",
                    data=str(ve),
                ),
            )
            # Use lower-level send to bypass object validation since session expects SessionMessage
            # We'll just write the dict directly to output if possible, or wrap it
            from mcp.shared.session import SessionMessage
            from mcp.types import ErrorData, JSONRPCMessage
            from mcp.types import JSONRPCError as McpJSONRPCError

            msg_id = getattr(message, "id", None) if hasattr(message, "id") else None
            mcp_error = McpJSONRPCError(
                jsonrpc="2.0",
                id=msg_id if msg_id is not None else "",
                error=ErrorData(
                    code=error_response.error.code,
                    message=error_response.error.message,
                    data=error_response.error.data,
                ),
            )
            fake_msg = JSONRPCMessage(root=mcp_error)
            await session.send_stream.send(SessionMessage(message=fake_msg))
        except Exception as e:
            logger.error(f"MCP Parsing/Execution Error: {e}")
            error_response = JSONRPCErrorResponse(
                jsonrpc="2.0",
                error=JSONRPCError(
                    code=-32700,
                    message="Parse error: Invalid JSON or bounded failure.",
                    data=str(e),
                ),
            )
            from mcp.shared.session import SessionMessage
            from mcp.types import ErrorData, JSONRPCMessage
            from mcp.types import JSONRPCError as McpJSONRPCError

            msg_id = getattr(message, "id", None) if hasattr(message, "id") else None
            mcp_error = McpJSONRPCError(
                jsonrpc="2.0",
                id=msg_id if msg_id is not None else "",
                error=ErrorData(
                    code=error_response.error.code,
                    message=error_response.error.message,
                    data=error_response.error.data,
                ),
            )
            fake_msg = JSONRPCMessage(root=mcp_error)
            await session.send_stream.send(SessionMessage(message=fake_msg))

    # Apply the monkeypatch shield
    Server._handle_message = _safe_handle_message  # type: ignore


def main() -> None:
    """Main entrypoint for the MCP Server using stdio transport."""
    _global_error_handler_shield()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
