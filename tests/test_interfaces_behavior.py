# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict, Optional
from coreason_manifest.spec.interfaces.behavior import IAgentRuntime, IResponseHandler, IStreamEmitter

class TestBehaviorProtocols:
    def test_structural_subtyping_check(self) -> None:
        """
        Verify that a concrete class implementing `assist` and `shutdown`
        satisfies the IAgentRuntime protocol.
        """
        class MockAgent:
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                pass

            async def shutdown(self) -> None:
                pass

        assert isinstance(MockAgent(), IAgentRuntime)

    def test_missing_method_check(self) -> None:
        """
        Verify that a class missing a required method does not satisfy the protocol.
        """
        class BadAgent:
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                pass
            # missing shutdown

        assert not isinstance(BadAgent(), IAgentRuntime)

    def test_response_handler_protocol(self) -> None:
        """
        Verify IResponseHandler protocol structure.
        """
        class MockHandler:
            async def emit_thought(self, content: str, source: str = "agent") -> None:
                pass

            async def create_text_stream(self, name: str) -> Any:
                return None

            async def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
                pass

            async def complete(self, outputs: Optional[Dict[str, Any]] = None) -> None:
                pass

        assert isinstance(MockHandler(), IResponseHandler)

    def test_stream_emitter_protocol(self) -> None:
        """
        Verify IStreamEmitter protocol structure.
        """
        class MockEmitter:
            async def emit_chunk(self, content: str) -> None:
                pass

            async def close(self) -> None:
                pass

        assert isinstance(MockEmitter(), IStreamEmitter)
