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
    and return strict JSON-RPC Error Envelopes. Also patches the stdio server stream
    reader to protect against massive JSON-Bomb string allocations before parsing.
    """
    import json
    import logging

    import mcp.server.stdio
    from mcp.server import Server
    from mcp.shared.session import BaseSession, SessionMessage
    from pydantic import ValidationError

    from coreason_manifest.adapters.mcp.schemas import JSONRPCError, JSONRPCErrorResponse

    logger = logging.getLogger(__name__)

    # 1. The Pre-Parsing Length Lock (JSON Bomb Defense)
    # FastMCP uses `stdio_server` which loops over `stdin`. We monkeypatch the `stdin_reader` generator logic
    # by intercepting the read line inside `mcp.server.stdio` natively.

    import sys
    from contextlib import asynccontextmanager
    from io import TextIOWrapper

    import anyio
    from mcp import types

    @asynccontextmanager
    async def safe_stdio_server(
        stdin: anyio.AsyncFile[str] | None = None,
        stdout: anyio.AsyncFile[str] | None = None,
    ):
        if not stdin:
            stdin = anyio.wrap_file(TextIOWrapper(sys.stdin.buffer, encoding="utf-8"))
        if not stdout:
            stdout = anyio.wrap_file(TextIOWrapper(sys.stdout.buffer, encoding="utf-8"))

        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        async def stdin_reader():
            try:
                async with read_stream_writer:
                    async for line in stdin:
                        # THE JSON-BOMB PRE-PARSING LOCK
                        if len(line) > 5_000_000:
                            # Reject explicitly without trying to decode
                            logger.error("JSON Bomb detected! Line length > 5MB")
                            await read_stream_writer.send(Exception("Parse error: Payload length exceeds 5MB limit."))
                            continue

                        try:
                            # 1. Manual parsing step for RFC strict error mapping
                            payload_dict = json.loads(line)
                        except json.JSONDecodeError as e:
                            # Complete parse failure -> id MUST be None
                            logger.error(f"JSON Decode Error: {e}")
                            await read_stream_writer.send(e)
                            continue

                        try:
                            message = types.JSONRPCMessage.model_validate(payload_dict)
                        except Exception as exc:
                            # Attach the dictionary so the handle_message shield can safely extract ID
                            exc._raw_payload_dict = payload_dict  # type: ignore
                            await read_stream_writer.send(exc)
                            continue

                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
            except anyio.ClosedResourceError:
                await anyio.lowlevel.checkpoint()

        async def stdout_writer():
            try:
                async with write_stream_reader:
                    async for session_message in write_stream_reader:
                        json_str = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                        await stdout.write(json_str + "\n")
                        await stdout.flush()
            except anyio.ClosedResourceError:
                await anyio.lowlevel.checkpoint()

        async with anyio.create_task_group() as tg:
            tg.start_soon(stdin_reader)
            tg.start_soon(stdout_writer)
            yield read_stream, write_stream

    mcp.server.stdio.stdio_server = safe_stdio_server

    # 2. The Global Exception Shield
    original_handle_message = Server._handle_message

    async def _safe_handle_message(
        self,
        message: Any,
        session: BaseSession,
        lifespan_context: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        from coreason_manifest.adapters.mcp.schemas import BoundedJSONRPCRequest

        req_id = None

        try:
            # If transport passed an exception directly
            if isinstance(message, Exception):
                # Safely extract ID if we managed to parse the dict but failed validation
                if hasattr(message, "_raw_payload_dict"):
                    req_id = message._raw_payload_dict.get("id")  # type: ignore
                raise message

            # Pre-validate the internal representation to ensure it adheres to boundary conditions
            if hasattr(message, "message") and hasattr(message.message, "model_dump"):
                raw_dict = message.message.model_dump(by_alias=True, exclude_none=True)
                req_id = raw_dict.get("id")
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
            from mcp.types import ErrorData, JSONRPCMessage
            from mcp.types import JSONRPCError as McpJSONRPCError

            mcp_error = McpJSONRPCError(
                jsonrpc="2.0",
                id=req_id,  # Valid JSON, but Invalid Request -> Returns req_id
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
            from mcp.types import ErrorData, JSONRPCMessage
            from mcp.types import JSONRPCError as McpJSONRPCError

            # RFC Specification: Parse errors (-32700) MUST return id as null.
            # FastMCP types might not allow None for id depending on version,
            # but RFC requires null. If the model forbids None, we bypass model_validate
            # and send the raw dictionary to guarantee RFC 2.0 compliance without crashing Pydantic.
            try:
                mcp_error = McpJSONRPCError(
                    jsonrpc="2.0",
                    id=None,  # type: ignore
                    error=ErrorData(
                        code=error_response.error.code,
                        message=error_response.error.message,
                        data=error_response.error.data,
                    ),
                )
                fake_msg = JSONRPCMessage(root=mcp_error)
                await session.send_stream.send(SessionMessage(message=fake_msg))
            except ValidationError:
                # Bypass validation to enforce RFC
                class RFCCompliantErrorMsg:
                    def model_dump_json(self, **_kwargs: Any) -> str:
                        return json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "id": None,
                                "error": {
                                    "code": error_response.error.code,
                                    "message": error_response.error.message,
                                    "data": error_response.error.data,
                                },
                            }
                        )

                    def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
                        return {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": error_response.error.code,
                                "message": error_response.error.message,
                                "data": error_response.error.data,
                            },
                        }

                class RFCCompliantSessionMsg:
                    message = RFCCompliantErrorMsg()

                await session.send_stream.send(RFCCompliantSessionMsg())  # type: ignore

    # Apply the monkeypatch shield
    Server._handle_message = _safe_handle_message  # type: ignore


def main() -> None:
    """Main entrypoint for the MCP Server using stdio transport."""
    _global_error_handler_shield()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
