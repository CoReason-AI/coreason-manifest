from collections.abc import Callable
from typing import Any

import pytest

from coreason_manifest.spec.core.engines import CodeExecutionReasoning, ComputerUseReasoning, StandardReasoning
from coreason_manifest.spec.core.flow import (
    AnyNode,
    Blackboard,
    DataSchema,
    EdgeSpec,
    FlowInterface,
    FlowMetadata,
    FlowSpec,
    Graph,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile


@pytest.fixture
def flow_metadata() -> FlowMetadata:
    return FlowMetadata(name="test", version="1.0.0", description="test", tags=[])


@pytest.fixture
def agent_node_factory() -> Callable[..., AgentNode]:
    def _create(nid: str, resilience: Any = None, tools: list[str] | None = None) -> AgentNode:
        return AgentNode(
            id=nid,
            type="agent",
            metadata={},
            profile=CognitiveProfile(role="r", persona="p"),
            tools=tools or [],
            resilience=resilience,
        )

    return _create


@pytest.fixture
def mock_flow_factory() -> Callable[[list[AnyNode], list[tuple[str, str]]], FlowSpec]:
    def _create(nodes_list: list[AnyNode], edges_list: list[tuple[str, str]]) -> FlowSpec:
        entry_point = nodes_list[0].id if nodes_list else "unknown"
        return FlowSpec(
            kind="FlowSpec",
            status="draft",
            metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
            interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
            blackboard=Blackboard(variables={}, persistence=None),
            graph=Graph(
                nodes={n.id: n for n in nodes_list},
                edges=[EdgeSpec(from_node=s, to_node=t) for s, t in edges_list],
                entry_point=entry_point,
            ),
        )

    return _create


@pytest.fixture
def safe_profile() -> CognitiveProfile:
    return CognitiveProfile(
        role="tester", persona="safe", reasoning=StandardReasoning(model="gpt-4-turbo"), fast_path=None
    )


@pytest.fixture
def unsafe_profile() -> CognitiveProfile:
    return CognitiveProfile(
        role="hacker",
        persona="unsafe",
        reasoning=ComputerUseReasoning(model="claude-3-5-sonnet"),
        fast_path=None,
    )


@pytest.fixture
def code_exec_profile() -> CognitiveProfile:
    return CognitiveProfile(
        role="coder",
        persona="unsafe_coder",
        reasoning=CodeExecutionReasoning(model="gpt-4", allow_network=True, timeout_seconds=10),
        fast_path=None,
    )
