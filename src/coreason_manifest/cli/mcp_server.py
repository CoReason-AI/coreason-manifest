# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import contextlib
import inspect
import json
import os
import re
from typing import Any, cast

from mcp.server.fastmcp import FastMCP
from pydantic import TypeAdapter

import coreason_manifest
from coreason_manifest.core import CoreasonBaseModel

# fmt: off
"""AGENT INSTRUCTION: This MCP Server is strictly passive. DO NOT register @mcp.tool() endpoints. Use @mcp.resource() for all ontological projections."""  # noqa: E501
# fmt: on

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


def _get_granted_licenses() -> set[str]:
    """Passively extracts the mathematically granted context from the environment."""
    env_val = os.environ.get("COREASON_GRANTED_LICENSES", "")
    if not env_val:
        return set()
    return {lic.strip() for lic in env_val.split(",") if lic.strip()}


def _is_schema_allowed(schema_dict: dict[str, Any], granted_licenses: set[str]) -> bool:
    """Calculates if the required license lattice is a strict subset of the granted lattice."""
    required = schema_dict.get("x-required-licenses", [])
    if not isinstance(required, list):
        required = []
    return set(required).issubset(granted_licenses)


@mcp.resource("schema://epistemic/{name}")
def get_epistemic_schema(name: str) -> str:
    """Returns the strict Pydantic JSON schema string for a specific requested model, governed by RBAC bounds."""
    if name not in _AVAILABLE_SCHEMAS:
        raise ValueError(f"Schema '{name}' not found in the manifest.")

    granted = _get_granted_licenses()
    schema_dict = cast("dict[str, Any]", _AVAILABLE_SCHEMAS[name])

    if not _is_schema_allowed(schema_dict, granted):
        # Zero-Trust: If not allowed, it cryptographically does not exist for this client.
        raise ValueError(f"Schema '{name}' not found in the manifest.")

    return json.dumps(schema_dict)


@mcp.resource("schema://state/memoized/{state_hash}")
def get_memoized_state(state_hash: str) -> str:
    """Returns a purely static/mock MemoizedNode JSON schema representation for the given hash."""
    if not re.match(r"^[a-f0-9]{64}$", state_hash):
        raise ValueError(f"Invalid hash format: '{state_hash}'. Must be a 64-character SHA-256 hex string.")

    # Return a static/mock representation.
    mock_schema = {
        "title": "MemoizedNode",
        "type": "object",
        "description": "Mock MemoizedNode representation",
        "properties": {
            "hash": {"title": "Hash", "type": "string", "const": state_hash},
            "type": {"title": "Type", "type": "string", "const": "memoized"},
        },
    }
    return json.dumps(mock_schema)


@mcp.resource("schema://capabilities/{profile}")
def get_capabilities_profile(profile: str) -> str:
    """
    Returns a JSON array string of allowed structural capabilities
    by intersecting the profile against profiles.py.
    """
    import coreason_manifest.compute.profiles as profiles_module

    profile_class = getattr(profiles_module, profile, None)
    if profile_class is None or not inspect.isclass(profile_class):
        raise ValueError(f"Profile '{profile}' not found in the capabilities definitions.")

    # Extract allowed structural capabilities from the profile class (Pydantic models)
    try:
        schema = profile_class.model_json_schema()
        capabilities = list(schema.get("properties", {}).keys())
    except Exception:
        capabilities = []

    return json.dumps(capabilities)


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
    from mcp.server.session import ServerSession
    from mcp.shared.session import SessionMessage  # type: ignore[attr-defined]
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

    MAX_PAYLOAD_BYTES = 5_000_000  # noqa: N806

    @asynccontextmanager
    async def safe_stdio_server(
        stdin: anyio.AsyncFile[str] | None = None,
        stdout: anyio.AsyncFile[str] | None = None,
    ) -> Any:
        # Get the underlying raw buffer if not explicitly mocked
        raw_stdin = sys.stdin.buffer if stdin is None else getattr(stdin, "_raw_buffer", sys.stdin.buffer)

        if not stdin:  # pragma: no cover
            stdin = anyio.wrap_file(TextIOWrapper(raw_stdin, encoding="utf-8"))
        if not stdout:  # pragma: no cover
            stdout = anyio.wrap_file(TextIOWrapper(sys.stdout.buffer, encoding="utf-8"))

        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        async def stdin_reader() -> None:
            try:
                async with read_stream_writer:
                    while True:
                        # DECLARATIVE GUILLOTINE: We enforce a physically bounded read at the OS/buffer level.
                        # This mathematically prevents unbounded buffer allocation during the read phase.
                        raw_line = await anyio.to_thread.run_sync(raw_stdin.readline, MAX_PAYLOAD_BYTES + 1)

                        if not raw_line:
                            break  # EOF reached safely

                        # THE JSON-BOMB PRE-PARSING LOCK
                        if len(raw_line) > MAX_PAYLOAD_BYTES:  # pragma: no cover
                            logger.error("JSON Bomb detected! Payload length > 5MB limit without delimiter.")
                            await read_stream_writer.send(Exception("Parse error: Payload length exceeds 5MB limit."))
                            break  # Sever the transport connection; do not attempt to process further

                        line = raw_line.decode("utf-8")

                        try:
                            # 1. Manual parsing step for RFC strict error mapping
                            payload_dict = await anyio.to_thread.run_sync(json.loads, line)
                        except json.JSONDecodeError as e:  # pragma: no cover
                            # Complete parse failure -> id MUST be None
                            logger.error(f"JSON Decode Error: {e}")
                            await read_stream_writer.send(e)
                            continue

                        try:
                            message = types.JSONRPCMessage.model_validate(payload_dict)
                        except Exception as exc:  # pragma: no cover
                            # Attach the dictionary so the handle_message shield can safely extract ID
                            exc._raw_payload_dict = payload_dict  # type: ignore
                            await read_stream_writer.send(exc)
                            continue

                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
            except anyio.ClosedResourceError:  # pragma: no cover
                await anyio.lowlevel.checkpoint()

        async def stdout_writer() -> None:
            try:
                async with write_stream_reader:
                    async for session_message in write_stream_reader:
                        json_str = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                        await stdout.write(json_str + "\n")
                        await stdout.flush()
            except anyio.ClosedResourceError:  # pragma: no cover
                await anyio.lowlevel.checkpoint()

        async with anyio.create_task_group() as tg:
            tg.start_soon(stdin_reader)
            tg.start_soon(stdout_writer)
            yield read_stream, write_stream

    mcp.server.stdio.stdio_server = safe_stdio_server

    # 2. The Global Exception Shield
    original_handle_message = Server._handle_message

    async def _safe_handle_message(
        self: Any,
        message: Any,
        session: ServerSession,
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
                if hasattr(message, "_raw_payload_dict"):  # pragma: no cover
                    req_id = message._raw_payload_dict.get("id")
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
            await session._write_stream.send(SessionMessage(message=fake_msg))
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
            try:  # pragma: no cover
                mcp_error = McpJSONRPCError(
                    jsonrpc="2.0",
                    id=None,
                    error=ErrorData(
                        code=error_response.error.code,
                        message=error_response.error.message,
                        data=error_response.error.data,
                    ),
                )
                fake_msg = JSONRPCMessage(root=mcp_error)
                await session._write_stream.send(SessionMessage(message=fake_msg))
            except ValidationError:  # pragma: no cover
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

                await session._write_stream.send(RFCCompliantSessionMsg())  # type: ignore

    # Apply the monkeypatch shield
    Server._handle_message = _safe_handle_message  # type: ignore


def main() -> None:  # pragma: no cover
    """Main entrypoint for the MCP Server using stdio transport."""
    _global_error_handler_shield()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
