# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Self, cast

from coreason_manifest.spec.core.co_intelligence import EscalationCriteria
from coreason_manifest.spec.core.engines import (
    FastPath,
    ReasoningConfig,
    StandardReasoning,
)
from coreason_manifest.spec.core.flow import (
    AnyNode,
    Blackboard,
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.spec.core.governance import (
    CircuitBreaker,
    ComputeLimits,
    DataLimits,
    FinancialLimits,
    Governance,
    OperationalPolicy,
)
from coreason_manifest.spec.core.memory import (
    EpisodicMemoryConfig,
    MemorySubsystem,
    ProceduralMemoryConfig,
    SemanticMemoryConfig,
    WorkingMemoryConfig,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, HumanNode, InspectorNode
from coreason_manifest.spec.core.resilience import (
    ErrorDomain,
    ErrorHandler,
    EscalationStrategy,
    FallbackStrategy,
    RecoveryStrategy,
    ResilienceConfig,
    RetryStrategy,
    SupervisionPolicy,
)
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.utils.validator import validate_flow


def create_resilience(
    retries: int,
    strategy: str = "escalate",
    backoff: float = 2.0,
    delay: float = 1.0,
    fallback_id: str | None = None,
    queue_name: str | None = None,
) -> ResilienceConfig:
    """Helper to create a ResilienceConfig."""
    res_strategy: RecoveryStrategy
    if strategy == "retry":
        res_strategy = RetryStrategy(
            max_attempts=retries,
            backoff_factor=backoff,
            initial_delay_seconds=delay,
        )
    elif strategy == "fallback":
        if not fallback_id:
            raise ValueError("fallback_id is required when strategy is 'fallback'")
        res_strategy = FallbackStrategy(fallback_node_id=fallback_id)
    else:
        # Default to escalate
        res_strategy = EscalationStrategy(
            queue_name=queue_name or "default_human_queue",
            notification_level="warning",
            timeout_seconds=3600,
            fallback_node_id=fallback_id,
        )

    return res_strategy


class AgentBuilder:
    """Fluent API to construct AgentNodes."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.role: str | None = None
        self.persona: str | None = None
        self.reasoning: ReasoningConfig | None = None
        self.fast_path: FastPath | None = None
        self.tools: list[str] = []
        self.resilience: ResilienceConfig | None = None
        self.operational_policy: OperationalPolicy | None = None
        self.escalation_rules: list[EscalationCriteria] = []
        self.memory: MemorySubsystem | None = None

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

    def with_resilience(
        self,
        retries: int,
        strategy: str = "escalate",
        backoff: float = 2.0,
        delay: float = 1.0,
        fallback_id: str | None = None,
        queue_name: str | None = None,
    ) -> "AgentBuilder":
        """Helper to configure AgentNode.resilience."""
        self.resilience = create_resilience(
            retries=retries,
            strategy=strategy,
            backoff=backoff,
            delay=delay,
            fallback_id=fallback_id,
            queue_name=queue_name,
        )
        return self

    def with_human_steering(self, timeout: int = 300, fallback_id: str | None = None) -> "AgentBuilder":
        """Configures resilience with a human escalation strategy."""
        esc_strategy = EscalationStrategy(
            queue_name="steering_queue",
            notification_level="info",
            timeout_seconds=timeout,
            fallback_node_id=fallback_id,
        )

        if self.resilience is None:
            self.resilience = esc_strategy
        elif isinstance(self.resilience, SupervisionPolicy):
            # Already a policy, append handler
            self.resilience.handlers.append(
                ErrorHandler(
                    match_domain=[ErrorDomain.SECURITY, ErrorDomain.CONTEXT],
                    strategy=esc_strategy,
                )
            )
        else:
            # Upgrade existing RecoveryStrategy to SupervisionPolicy
            # Preserving existing strategy for transient errors
            old_strategy = self.resilience

            # Dynamic limit calculation if max_attempts is available
            max_actions = 10
            if hasattr(old_strategy, "max_attempts"):
                # Ensure global limit accommodates the retry strategy + 1 for escalation
                # Use getattr to avoid type checking issues with Union members that might not have max_attempts
                attempts = getattr(old_strategy, "max_attempts", 0)
                if isinstance(attempts, int):
                    max_actions = max(10, attempts + 1)

            self.resilience = SupervisionPolicy(
                handlers=[
                    ErrorHandler(
                        match_domain=[ErrorDomain.LLM, ErrorDomain.SYSTEM, ErrorDomain.TIMEOUT, ErrorDomain.RESOURCE],
                        strategy=old_strategy,
                    ),
                    ErrorHandler(
                        match_domain=[ErrorDomain.SECURITY, ErrorDomain.CONTEXT, ErrorDomain.DATA, ErrorDomain.CLIENT],
                        strategy=esc_strategy,
                    ),
                ],
                default_strategy=esc_strategy,  # Fallback to escalation
                max_cumulative_actions=max_actions,
            )
        return self

    def with_operational_policy(
        self,
        max_cost_usd: float | None = None,
        max_tokens: int | None = None,
        fallback_model: str | None = None,
        max_steps: int | None = None,
        max_execution_time_seconds: int | None = None,
        max_rows_per_query: int | None = None,
        max_payload_bytes: int | None = None,
        max_search_results: int | None = None,
    ) -> "AgentBuilder":
        """Configures the operational limits (Financial, Compute, Data)."""
        financial = None
        if max_cost_usd is not None or max_tokens is not None or fallback_model is not None:
            financial = FinancialLimits(
                max_cost_usd=max_cost_usd,
                max_tokens_total=max_tokens,
                budget_depletion_routing=fallback_model,
            )

        compute = None
        if max_steps is not None or max_execution_time_seconds is not None:
            compute = ComputeLimits(
                max_cognitive_steps=max_steps, max_execution_time_seconds=max_execution_time_seconds
            )

        data = None
        if max_rows_per_query is not None or max_payload_bytes is not None or max_search_results is not None:
            data = DataLimits(
                max_rows_per_query=max_rows_per_query,
                max_payload_bytes=max_payload_bytes,
                max_search_results=max_search_results,
            )

        if financial or compute or data:
            self.operational_policy = OperationalPolicy(financial=financial, compute=compute, data=data)
        return self

    def with_escalation_rule(
        self, condition: str, role: str, strategy: EscalationStrategy | None = None
    ) -> "AgentBuilder":
        """Adds a local escalation rule to the agent."""
        self.escalation_rules.append(EscalationCriteria(condition=condition, role=role, strategy=strategy))
        return self

    def with_memory(
        self,
        working_limit: int = 4096,
        enable_paging: bool = False,
        salience_threshold: float | None = None,
        consolidation_interval: int | None = None,
        graph_namespace: str | None = None,
        bitemporal_tracking: bool = False,
        allowed_entity_types: list[str] | None = None,
        skill_library_ref: str | None = None,
    ) -> "AgentBuilder":
        """Configures the memory subsystem."""
        working = WorkingMemoryConfig(max_tokens=working_limit, enable_active_paging=enable_paging)

        episodic = None
        if salience_threshold is not None:
            episodic = EpisodicMemoryConfig(
                salience_threshold=salience_threshold,
                consolidation_interval_turns=consolidation_interval,
            )

        semantic = None
        if graph_namespace is not None:
            semantic = SemanticMemoryConfig(
                graph_namespace=graph_namespace,
                bitemporal_tracking=bitemporal_tracking,
                allowed_entity_types=allowed_entity_types,
            )

        procedural = None
        if skill_library_ref is not None:
            procedural = ProceduralMemoryConfig(skill_library_ref=skill_library_ref)

        self.memory = MemorySubsystem(
            working=working,
            episodic=episodic,
            semantic=semantic,
            procedural=procedural,
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
            memory=self.memory,
        )

        return AgentNode(
            id=self.agent_id,
            metadata={},
            resilience=self.resilience,
            type="agent",
            profile=profile,
            tools=self.tools,
            operational_policy=self.operational_policy,
            escalation_rules=self.escalation_rules,
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

    def set_operational_policy(
        self,
        max_cost_usd: float | None = None,
        max_tokens: int | None = None,
        fallback_model: str | None = None,
        max_steps: int | None = None,
        max_execution_time_seconds: int | None = None,
        max_concurrent_agents: int | None = None,
        max_rows_per_query: int | None = None,
        max_payload_bytes: int | None = None,
        max_search_results: int | None = None,
    ) -> Self:
        """Configures global operational limits (Financial, Data, Compute)."""
        financial = None
        if max_cost_usd is not None or max_tokens is not None or fallback_model is not None:
            financial = FinancialLimits(
                max_cost_usd=max_cost_usd,
                max_tokens_total=max_tokens,
                budget_depletion_routing=fallback_model,
            )

        data = None
        if max_rows_per_query is not None or max_payload_bytes is not None or max_search_results is not None:
            data = DataLimits(
                max_rows_per_query=max_rows_per_query,
                max_payload_bytes=max_payload_bytes,
                max_search_results=max_search_results,
            )

        compute = None
        if max_steps is not None or max_execution_time_seconds is not None or max_concurrent_agents is not None:
            compute = ComputeLimits(
                max_cognitive_steps=max_steps,
                max_execution_time_seconds=max_execution_time_seconds,
                max_concurrent_agents=max_concurrent_agents,
            )

        op_policy = OperationalPolicy(financial=financial, data=data, compute=compute)

        if self.governance:
            self.governance = self.governance.model_copy(update={"operational_policy": op_policy})
        else:
            self.governance = Governance(operational_policy=op_policy)
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

    def _register_node(self, node: AnyNode) -> None:
        """Registers a node to the flow. Must be implemented by subclasses."""
        raise NotImplementedError

    def add_agent_ref(self, node_id: str, profile_id: str, tools: list[str] | None = None) -> Self:
        """Adds a node that points to a registered profile."""
        if tools is None:
            tools = []
        node = AgentNode(
            id=node_id,
            metadata={},
            resilience=None,
            type="agent",
            profile=profile_id,
            tools=tools,
        )
        self._register_node(node)
        return self

    def add_shadow_node(self, node_id: str, prompt: str, shadow_timeout: int = 60) -> Self:
        """Adds a human shadow node to the flow."""
        node = HumanNode(
            id=node_id,
            metadata={},
            type="human",
            prompt=prompt,
            interaction_mode="shadow",
            escalation=EscalationStrategy(
                queue_name="shadow_queue",
                notification_level="info",
                timeout_seconds=shadow_timeout,
            ),
        )
        self._register_node(node)
        return self

    def add_inspector(self, node_id: str, target: str, criteria: str, output: str, pass_threshold: float = 0.5) -> Self:
        """Adds an inspector node to the flow."""
        node = InspectorNode(
            id=node_id,
            metadata={},
            target_variable=target,
            criteria=criteria,
            pass_threshold=pass_threshold,
            output_variable=output,
            optimizer=None,
            type="inspector",
        )
        self._register_node(node)
        return self

    def _create_flow_instance(self) -> LinearFlow | GraphFlow:
        """Abstract method to create the specific Flow instance."""
        raise NotImplementedError

    def build(self) -> LinearFlow | GraphFlow:
        """Constructs and validates the Flow object."""
        flow = self._create_flow_instance()

        errors = validate_flow(flow)
        if errors:
            # Format structured errors into string for ValueError
            error_msgs = [f"[{e.code}] {e.message}" for e in errors]
            raise ValueError("Validation failed:\n- " + "\n- ".join(error_msgs))

        return flow


class NewLinearFlow(BaseFlowBuilder):
    """Fluent API to construct LinearFlows programmatically."""

    def __init__(self, name: str, version: str = "0.1.0", description: str = "") -> None:
        super().__init__(name, version, description)
        self.steps: list[AnyNode] = []

    def _register_node(self, node: AnyNode) -> None:
        self.steps.append(node)

    def add_step(self, node: AnyNode) -> "NewLinearFlow":
        """Appends a node to the sequence."""
        self.steps.append(node)
        return self

    def add_agent(self, agent: AgentNode) -> "NewLinearFlow":
        """Appends an agent node to the sequence."""
        self.steps.append(agent)
        return self

    def _create_flow_instance(self) -> LinearFlow:
        return LinearFlow(
            kind="LinearFlow",
            status="published",
            metadata=self.metadata,
            steps=self.steps,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

    def build(self) -> LinearFlow:
        # Override return type hint for better IDE support, but reuse base implementation
        return cast("LinearFlow", super().build())


class NewGraphFlow(BaseFlowBuilder):
    """Fluent API to construct GraphFlows programmatically."""

    def __init__(self, name: str, version: str = "0.1.0", description: str = "") -> None:
        super().__init__(name, version, description)
        self._nodes: dict[str, AnyNode] = {}
        self._edges: list[Edge] = []
        self._entry_point: str | None = None
        # Defaults
        self.interface = FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        )
        self.blackboard: Blackboard | None = None

    def _register_node(self, node: AnyNode) -> None:
        self._nodes[node.id] = node

    def set_entry_point(self, node_id: str) -> "NewGraphFlow":
        """Sets the explicit entry point for the graph."""
        self._entry_point = node_id
        return self

    def add_node(self, node: AnyNode) -> "NewGraphFlow":
        """Adds a node to the graph."""
        self._nodes[node.id] = node
        return self

    def add_agent(self, agent: AgentNode) -> "NewGraphFlow":
        """Adds an agent node to the graph."""
        self._nodes[agent.id] = agent
        return self

    def connect(self, source: str, target: str, condition: str | None = None) -> "NewGraphFlow":
        """Adds an edge to the graph."""
        self._edges.append(Edge(from_node=source, to_node=target, condition=condition))
        return self

    def set_interface(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> "NewGraphFlow":
        """Defines the Input/Output contract for the Flow."""
        self.interface = FlowInterface(
            inputs=DataSchema(json_schema=inputs),
            outputs=DataSchema(json_schema=outputs),
        )
        return self

    def set_blackboard(self, variables: dict[str, VariableDef], persistence: bool = False) -> "NewGraphFlow":
        """Configures the shared memory blackboard."""
        self.blackboard = Blackboard(variables=variables, persistence=persistence)
        return self

    def _create_flow_instance(self) -> GraphFlow:
        # Determine entry point
        ep = self._entry_point
        if not ep:
            ep = next(iter(self._nodes.keys())) if self._nodes else "missing_entry_point"

        graph = Graph(nodes=self._nodes, edges=self._edges, entry_point=ep)

        # KEY: All nodes in a static GraphFlow built via this builder are considered
        # "Fixed Recipes" and should be immutable by default in the runtime.
        # We simulate this by pre-populating the lock set.
        for node_id in self._nodes:
            graph._locked_nodes.add(node_id)

        return GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=self.metadata,
            interface=self.interface,
            blackboard=self.blackboard,
            graph=graph,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

    def build(self) -> GraphFlow:
        # Override return type hint
        return cast("GraphFlow", super().build())
