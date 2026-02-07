# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import typing
from typing import get_type_hints

import pytest
from coreason_manifest.spec.common.request import AgentRequest
from coreason_manifest.spec.common.session import SessionState
from coreason_manifest.spec.interfaces.behavior import (
    IAgentRuntime,
    IResponseHandler,
    IStreamEmitter,
)


class MockAgent:
    async def assist(self, session: SessionState, request: AgentRequest, handler: IResponseHandler) -> None:
        pass

    async def shutdown(self) -> None:
        pass


class BadAgent:
    async def shutdown(self) -> None:
        pass


def test_protocol_adherence() -> None:
    """Verify that MockAgent implements IAgentRuntime and BadAgent does not."""
    assert isinstance(MockAgent(), IAgentRuntime)
    assert not isinstance(BadAgent(), IAgentRuntime)


def test_type_hinting_resolution() -> None:
    """Verify that type hints resolve correctly for IAgentRuntime.assist."""
    # Since imports are under TYPE_CHECKING, we must provide the context
    hints = get_type_hints(IAgentRuntime.assist, globalns=globals())
    assert hints["session"] is SessionState
    assert hints["request"] is AgentRequest
    assert hints["handler"] is IResponseHandler
    assert hints["return"] is type(None)
