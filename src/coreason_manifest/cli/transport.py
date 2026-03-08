# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: STRICTLY KINETIC BOUNDARY.
This module contains isolated execution loops and I/O stream interception for the CLI.
YOU ARE EXPLICITLY FORBIDDEN from importing this module back into the `adapters/` or core data planes.
"""

import asyncio
import json
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp.shared.session import SessionMessage  # type: ignore[attr-defined]
from mcp.types import JSONRPCMessage
from pydantic import ValidationError

from coreason_manifest.adapters.mcp.schemas import BoundedJSONRPCRequest


@asynccontextmanager
async def secure_stdio_server() -> AsyncGenerator[tuple[MemoryObjectReceiveStream[Any], MemoryObjectSendStream[Any]]]:
    """
    A secure drop-in replacement for mcp.server.stdio.stdio_server.
    Intercepts raw stdin, prevents JSON-bomb/recursion DoS attacks,
    and outputs RFC-compliant JSON-RPC 2.0 errors directly to stdout.
    """
    send_to_server, receive_from_client = anyio.create_memory_object_stream(256)
    send_to_client, receive_from_server = anyio.create_memory_object_stream(256)

    def _write_error(code: int, msg: str) -> None:
        error_response = {"jsonrpc": "2.0", "error": {"code": code, "message": msg}, "id": None}
        sys.stdout.write(json.dumps(error_response) + "\n")
        sys.stdout.flush()

    async def _read_stdin() -> None:
        try:
            loop = asyncio.get_running_loop()
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)

            async with send_to_server:
                while True:
                    line = await reader.readline()
                    if not line:
                        break

                    if len(line) > 5_000_000:
                        _write_error(-32700, "Parse error: Payload length exceeds 5MB limit.")
                        continue

                    raw_payload = line.decode("utf-8").strip()
                    if not raw_payload:
                        continue

                    try:
                        payload_dict = json.loads(raw_payload)
                        # ENFORCE SCHEMA BOUNDARIES
                        BoundedJSONRPCRequest.model_validate(payload_dict)
                        # PASS TO MCP
                        message = JSONRPCMessage.model_validate(payload_dict)
                        await send_to_server.send(SessionMessage(message=message))
                    except (json.JSONDecodeError, ValidationError) as e:
                        code = -32600 if isinstance(e, ValidationError) else -32700
                        _write_error(code, f"Validation/Parse error: {e!s}")
        except anyio.ClosedResourceError:
            pass
        except Exception:  # noqa: S110
            pass

    async def _write_stdout() -> None:
        try:
            async with receive_from_server:
                async for session_message in receive_from_server:
                    out_str = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                    sys.stdout.write(out_str + "\n")
                    sys.stdout.flush()
        except anyio.ClosedResourceError:
            pass

    async with anyio.create_task_group() as tg:
        tg.start_soon(_read_stdin)
        tg.start_soon(_write_stdout)
        try:
            yield receive_from_client, send_to_client
        finally:
            tg.cancel_scope.cancel()
