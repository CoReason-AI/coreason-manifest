# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Self

from coreason_manifest.spec.core.engines import (
    FastPath,
    ReasoningConfig,
    StandardReasoning,
)
from coreason_manifest.spec.core.flow import (
    AnyNode,
    Blackboard,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, InspectorNode
from coreason_manifest.spec.core.resilience import (
    EscalationStrategy,
    FallbackStrategy,
    RetryStrategy,
    SupervisionPolicy,
)
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.utils.validator import validate_flow


def create_supervision(
    retries: int,
    strategy: str = "escalate",
    backoff: float = 2.0,
    delay: float = 1.0,
    fallback_id: str | None = None,
    queue_name: str | None = None,
) -> SupervisionPolicy:
    """Helper to create a SupervisionPolicy."""
    res_strategy: Any
    if strategy == "retry":
        res_strategy = RetryStrategy(
            max_attempts=retries,
            backoff_factor=backoff,
            initial_delay_seconds=delay,
        )
    elif strategy == "fallback":
        # if not fallback_id, Pydantic will raise ValidationError
        res_strategy = FallbackStrategy(
            fallback_node_id=fallback_id,  # type: ignore
        )
    else:
        # Default to escalate
        res_strategy = EscalationStrategy(
            queue_name=queue_name or "default_human_queue",
            notification_level="warning",
            timeout_seconds=3600,
        )

    return SupervisionPolicy(
        handlers=[],
        default_strategy=res_strategy,
    )


class AgentBuilder:
    """Fluent API to construct AgentNodes."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.role: str | None = None
        self.persona: str | None = None
        self.reasoning: ReasoningConfig | None = None
        self.fast_path: FastPath | None = None
        self.tools: list[str] = []
        self.supervision: SupervisionPolicy | None = None

    def with_identity(self, role: str, persona: str) -> "AgentBuilder":
        """Configures CognitiveProfile.role and CognitiveProfile.persona."""
        self.role = role
        self.persona = persona
        return self

    def with_reasoning(self, model: str, thoughts_max: int = 5, min_confidence: float = 0.7) -> "AgentBuilder":
        """Configures CognitiveProfile.reasoning (Standard CoT)."""
        self.reasoning = StandardReasoning(model=model, thoughts_max=thoughts_max, min_confidence=min_confidence)
        return self

    def with_fast_path(self, model: str, timeout_ms: int = 1000, caching: bool = True) -> "AgentBuilder":
        """Configures CognitiveProfile.fast_path."""
        self.fast_path = FastPath(model=model, timeout_ms=timeout_ms, caching=caching)
        return self

    def with_tools(self, tools: list[str]) -> "AgentBuilder":
        """Appends to AgentNode.tools."""
        self.tools.extend(tools)
        return self

    def with_supervision(
        self,
        retries: int,
        strategy: str = "escalate",
        backoff: float = 2.0,
        delay: float = 1.0,
        fallback_id: str | None = None,
        queue_name: str | None = None,
    ) -> "AgentBuilder":
        """Helper to configure AgentNode.supervision."""
        self.supervision = create_supervision(
            retries=retries,
            strategy=strategy,
            backoff=backoff,
            delay=delay,
            fallback_id=fallback_id,
            queue_name=queue_name,
        )
        return self

    def build(self) -> AgentNode:
        """Validates and returns the node."""
        if not self.role or not self.persona:
            raise ValueError("Agent identity (role, persona) must be set.")

        profile = CognitiveProfile(
            role=self.role,
            persona=self.persona,
            reasoning=self.reasoning,
            fast_path=self.fast_path,
        )

        return AgentNode(
            id=self.agent_id,
            metadata={},
            supervision=self.supervision,
            type="agent",
            profile=profile,
            tools=self.tools,
        )


class BaseFlowBuilder:
    """Shared logic for all flow builders to enforce DRY principles."""

    def __init__(self, name: str, version: str, description: str) -> None:
        self.metadata = FlowMetadata(name=name, version=version, description=description, tags=[])
        self._profiles: dict[str, CognitiveProfile] = {}
        self._tool_packs: dict[str, ToolPack] = {}
        self._supervision_templates: dict[str, SupervisionPolicy] = {}
        self.governance: Governance | None = None

    def define_supervision_template(self, template_id: str, policy: SupervisionPolicy) -> Self:
        """Registers a reusable supervision policy."""
        self._supervision_templates[template_id] = policy
        return self

    def define_profile(
        self,
        profile_id: str,
        role: str,
        persona: str,
        reasoning: ReasoningConfig | None = None,
        fast_path: FastPath | None = None,
    ) -> Self:
        """Registers a reusable profile definition."""
        self._profiles[profile_id] = CognitiveProfile(
            role=role, persona=persona, reasoning=reasoning, fast_path=fast_path
        )
        return self

    def add_tool_pack(self, pack: ToolPack) -> Self:
        """Adds a tool pack to the flow."""
        self._tool_packs[pack.namespace] = pack
        return self

    def set_governance(self, gov: Governance) -> Self:
        """Sets the governance policy."""
        self.governance = gov
        return self

    def set_circuit_breaker(self, error_threshold: int, reset_timeout: int, fallback_node: str | None = None) -> Self:
        """Sets the circuit breaker policy."""
        cb = CircuitBreaker(
            error_threshold_count=error_threshold,
            reset_timeout_seconds=reset_timeout,
            fallback_node_id=fallback_node,
        )
        if self.governance:
            self.governance = self.governance.model_copy(update={"circuit_breaker": cb})
        else:
            self.governance = Governance(circuit_breaker=cb)
        return self

    def _build_definitions(self) -> FlowDefinitions:
        """Helper to build FlowDefinitions from registered components."""
        return FlowDefinitions(
            profiles=self._profiles,
            tool_packs=self._tool_packs,
            supervision_templates=self._supervision_templates,
        )


class NewLinearFlow(BaseFlowBuilder):
    """Fluent API to construct LinearFlows programmatically."""

    def __init__(self, name: str, version: str = "0.1", description: str = "") -> None:
        super().__init__(name, version, description)
        self.sequence: list[AnyNode] = []

    def add_step(self, node: AnyNode) -> "NewLinearFlow":
        """Appends a node to the sequence."""
        self.sequence.append(node)
        return self

    def add_agent(self, agent: AgentNode) -> "NewLinearFlow":
        """Appends an agent node to the sequence."""
        self.sequence.append(agent)
        return self

    def add_agent_ref(self, node_id: str, profile_id: str, tools: list[str] | None = None) -> "NewLinearFlow":
        """Adds a node that points to a registered profile."""
        if tools is None:
            tools = []
        node = AgentNode(
            id=node_id,
            metadata={},
            supervision=None,
            type="agent",
            profile=profile_id,
            tools=tools,
        )
        self.sequence.append(node)
        return self

    def add_inspector(
        self, node_id: str, target: str, criteria: str, output: str, pass_threshold: float = 0.5
    ) -> "NewLinearFlow":
        """Adds an inspector node to the sequence."""
        node = InspectorNode(
            id=node_id,
            metadata={},
            supervision=None,
            target_variable=target,
            criteria=criteria,
            pass_threshold=pass_threshold,
            output_variable=output,
            optimizer=None,
            type="inspector",
        )
        self.sequence.append(node)
        return self

    def build(self) -> LinearFlow:
        """Constructs and validates the LinearFlow object."""
        flow = LinearFlow(
            kind="LinearFlow",
            metadata=self.metadata,
            sequence=self.sequence,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

        errors = validate_flow(flow)
        if errors:
            raise ValueError("Validation failed:\n- " + "\n- ".join(errors))

        return flow


class NewGraphFlow(BaseFlowBuilder):
    """Fluent API to construct GraphFlows programmatically."""

    def __init__(self, name: str, version: str = "0.1", description: str = "") -> None:
        super().__init__(name, version, description)
        self._nodes: dict[str, AnyNode] = {}
        self._edges: list[Edge] = []
        # Defaults
        self.interface = FlowInterface(inputs={}, outputs={})
        self.blackboard: Blackboard | None = None

    def add_node(self, node: AnyNode) -> "NewGraphFlow":
        """Adds a node to the graph."""
        self._nodes[node.id] = node
        return self

    def add_agent(self, agent: AgentNode) -> "NewGraphFlow":
        """Adds an agent node to the graph."""
        self._nodes[agent.id] = agent
        return self

    def add_agent_ref(self, node_id: str, profile_id: str, tools: list[str] | None = None) -> "NewGraphFlow":
        """Adds a node that points to a registered profile."""
        if tools is None:
            tools = []
        node = AgentNode(
            id=node_id,
            metadata={},
            supervision=None,
            type="agent",
            profile=profile_id,
            tools=tools,
        )
        self._nodes[node.id] = node
        return self

    def add_inspector(
        self, node_id: str, target: str, criteria: str, output: str, pass_threshold: float = 0.5
    ) -> "NewGraphFlow":
        """Adds an inspector node to the graph."""
        node = InspectorNode(
            id=node_id,
            metadata={},
            supervision=None,
            target_variable=target,
            criteria=criteria,
            pass_threshold=pass_threshold,
            output_variable=output,
            optimizer=None,
            type="inspector",
        )
        self._nodes[node.id] = node
        return self

    def connect(self, source: str, target: str, condition: str | None = None) -> "NewGraphFlow":
        """Adds an edge to the graph."""
        self._edges.append(Edge(source=source, target=target, condition=condition))
        return self

    def set_interface(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> "NewGraphFlow":
        """Defines the Input/Output contract for the Flow."""
        self.interface = FlowInterface(inputs=inputs, outputs=outputs)
        return self

    def set_blackboard(self, variables: dict[str, VariableDef], persistence: bool = False) -> "NewGraphFlow":
        """Configures the shared memory blackboard."""
        self.blackboard = Blackboard(variables=variables, persistence=persistence)
        return self

    def build(self) -> GraphFlow:
        """Constructs and validates the GraphFlow object."""
        graph = Graph(nodes=self._nodes, edges=self._edges)

        flow = GraphFlow(
            kind="GraphFlow",
            metadata=self.metadata,
            interface=self.interface,
            blackboard=self.blackboard,
            graph=graph,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

        errors = validate_flow(flow)
        if errors:
            raise ValueError("Validation failed:\n- " + "\n- ".join(errors))

        return flow
