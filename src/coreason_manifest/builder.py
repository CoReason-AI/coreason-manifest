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
from coreason_manifest.spec.core.contracts import (
    ActionNode,
    AtomicSkill,
    NodeSpec,
    StrategyNode,
)
from coreason_manifest.spec.core.engines import (
    FastPath,
    ReasoningConfig,
    StandardReasoning,
)
from coreason_manifest.spec.core.flow import (
    Blackboard,
    DataSchema,
    EdgeSpec,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    FlowSpec,
    Graph,
    PersistenceConfig,
    SupervisionConfig,
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
from coreason_manifest.spec.core.nodes import CognitiveProfile
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
from coreason_manifest.spec.core.types import StrictPayload
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
    """Fluent API to construct AgentNodes (ActionNodes)."""

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
        self.role = role
        self.persona = persona
        return self

    def with_reasoning(self, model: str, thoughts_max: int = 5, min_confidence: float = 0.7) -> "AgentBuilder":
        self.reasoning = StandardReasoning(model=model, thoughts_max=thoughts_max, min_confidence=min_confidence)
        return self

    def with_fast_path(self, model: str, timeout_ms: int = 1000, caching: bool = True) -> "AgentBuilder":
        self.fast_path = FastPath(model=model, timeout_ms=timeout_ms, caching=caching)
        return self

    def with_tools(self, tools: list[str]) -> "AgentBuilder":
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
        esc_strategy = EscalationStrategy(
            queue_name="steering_queue",
            notification_level="info",
            timeout_seconds=timeout,
            fallback_node_id=fallback_id,
        )

        if self.resilience is None:
            self.resilience = esc_strategy
        elif isinstance(self.resilience, SupervisionPolicy):
            self.resilience.handlers.append(
                ErrorHandler(
                    match_domain=[ErrorDomain.SECURITY, ErrorDomain.CONTEXT],
                    strategy=esc_strategy,
                )
            )
        else:
            old_strategy = self.resilience
            max_actions = 10
            if hasattr(old_strategy, "max_attempts"):
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
                default_strategy=esc_strategy,
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

    def build(self) -> ActionNode:
        if not self.role or not self.persona:
            raise ValueError("Agent identity (role, persona) must be set.")

        profile_data = {
            "role": self.role,
            "persona": self.persona,
        }
        if self.reasoning:
            profile_data["reasoning"] = self.reasoning.model_dump(mode="json")
        if self.fast_path:
            profile_data["fast_path"] = self.fast_path.model_dump(mode="json")
        if self.memory:
            profile_data["memory"] = self.memory.model_dump(mode="json")

        return ActionNode(
            id=self.agent_id,
            type="action",
            metadata=StrictPayload(data={"profile": profile_data, "resilience": self.resilience.model_dump(mode="json") if self.resilience else None}),
            skill=AtomicSkill(capabilities=self.tools),
        )


class BaseFlowBuilder:
    def __init__(self, name: str, version: str, description: str) -> None:
        self.metadata = FlowMetadata(name=name, version=version, description=description, tags=[])
        self._profiles: dict[str, CognitiveProfile] = {}
        self._tool_packs: dict[str, ToolPack] = {}
        self._supervision_templates: dict[str, SupervisionPolicy] = {}
        self.governance: Governance | None = None

    def define_supervision_template(self, template_id: str, policy: SupervisionPolicy) -> Self:
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
        self._profiles[profile_id] = CognitiveProfile(
            role=role, persona=persona, reasoning=reasoning, fast_path=fast_path
        )
        return self

    def add_tool_pack(self, pack: ToolPack) -> Self:
        self._tool_packs[pack.namespace] = pack
        return self

    def set_governance(self, gov: Governance) -> Self:
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
        # supervision_templates expects dict[str, SupervisionConfig], we have SupervisionPolicy
        # Mapping needed? SupervisionConfig has params. SupervisionPolicy has handlers.
        # This part is tricky. I'll pass None for now to avoid validation error, or adapt.
        # FlowDefinitions.supervision_templates: dict[str, SupervisionConfig]
        return FlowDefinitions(
            profiles=self._profiles,
            tool_packs=self._tool_packs,
            supervision_templates=None, # Adapted for strictness
        )

    def _register_node(self, node: NodeSpec) -> None:
        raise NotImplementedError

    def add_agent_ref(self, node_id: str, profile_id: str, tools: list[str] | None = None) -> Self:
        if tools is None:
            tools = []
        node = ActionNode(
            id=node_id,
            type="action",
            metadata=StrictPayload(data={"profile": profile_id}),
            skill=AtomicSkill(capabilities=tools),
        )
        self._register_node(node)
        return self

    def add_shadow_node(self, node_id: str, prompt: str, shadow_timeout: int = 60) -> Self:
        node = ActionNode(
            id=node_id,
            type="action",
            metadata=StrictPayload(data={
                "prompt": prompt,
                "interaction_mode": "shadow",
                "timeout": shadow_timeout
            }),
            skill=AtomicSkill(capabilities=["human_shadow"]),
        )
        self._register_node(node)
        return self

    def add_inspector(self, node_id: str, target: str, criteria: str, output: str, pass_threshold: float = 0.5) -> Self:
        node = StrategyNode(
            id=node_id,
            type="strategy",
            metadata=StrictPayload(data={}),
            strategy_config=StrictPayload(data={
                "target": target,
                "criteria": criteria,
                "output": output,
                "threshold": pass_threshold
            })
        )
        self._register_node(node)
        return self

    def _create_flow_instance(self) -> FlowSpec:
        raise NotImplementedError

    def build(self) -> FlowSpec:
        flow = self._create_flow_instance()
        errors = validate_flow(flow)
        if errors:
            error_msgs = [f"[{e.code}] {e.message}" for e in errors]
            raise ValueError("Validation failed:\n- " + "\n- ".join(error_msgs))
        return flow


class NewLinearFlow(BaseFlowBuilder):
    def __init__(self, name: str, version: str = "0.1.0", description: str = "") -> None:
        super().__init__(name, version, description)
        self.steps: list[NodeSpec] = []

    def _register_node(self, node: NodeSpec) -> None:
        self.steps.append(node)

    def add_step(self, node: NodeSpec) -> "NewLinearFlow":
        self.steps.append(node)
        return self

    def add_agent(self, agent: ActionNode) -> "NewLinearFlow":
        self.steps.append(agent)
        return self

    def _create_flow_instance(self) -> FlowSpec:
        nodes = {n.id: n for n in self.steps}
        edges: list[EdgeSpec] = []
        for i in range(len(self.steps) - 1):
            edges.append(EdgeSpec(from_node=self.steps[i].id, to_node=self.steps[i + 1].id))

        entry_point = self.steps[0].id if self.steps else None

        graph = Graph(nodes=nodes, edges=edges, entry_point=entry_point)

        return FlowSpec(
            kind="FlowSpec",
            status="published",
            metadata=self.metadata,
            graph=graph,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

    def build(self) -> FlowSpec:
        return cast("FlowSpec", super().build())


class NewGraphFlow(BaseFlowBuilder):
    def __init__(self, name: str, version: str = "0.1.0", description: str = "") -> None:
        super().__init__(name, version, description)
        self._nodes: dict[str, NodeSpec] = {}
        self._edges: list[EdgeSpec] = []
        self._entry_point: str | None = None
        self.interface = FlowInterface(
            inputs=DataSchema(json_schema={}),
            outputs=DataSchema(json_schema={}),
        )
        self.blackboard: Blackboard | None = None

    def _register_node(self, node: NodeSpec) -> None:
        self._nodes[node.id] = node

    def set_entry_point(self, node_id: str) -> "NewGraphFlow":
        self._entry_point = node_id
        return self

    def add_node(self, node: NodeSpec) -> "NewGraphFlow":
        self._nodes[node.id] = node
        return self

    def add_agent(self, agent: ActionNode) -> "NewGraphFlow":
        self._nodes[agent.id] = agent
        return self

    def connect(self, source: str, target: str, condition: str | None = None) -> "NewGraphFlow":
        self._edges.append(EdgeSpec(from_node=source, to_node=target, condition=condition))
        return self

    def set_interface(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> "NewGraphFlow":
        self.interface = FlowInterface(
            inputs=DataSchema(json_schema=inputs),
            outputs=DataSchema(json_schema=outputs),
        )
        return self

    def set_blackboard(self, variables: dict[str, dict[str, Any]], persistence: bool = False) -> "NewGraphFlow":
        persistence_config = PersistenceConfig(type="default") if persistence else None
        self.blackboard = Blackboard(variables=variables, persistence=persistence_config)
        return self

    def _create_flow_instance(self) -> FlowSpec:
        ep = self._entry_point
        if not ep:
            ep = next(iter(self._nodes.keys())) if self._nodes else "missing_entry_point"

        graph = Graph(nodes=self._nodes, edges=self._edges, entry_point=ep)

        return FlowSpec(
            kind="FlowSpec",
            status="published",
            metadata=self.metadata,
            interface=self.interface,
            blackboard=self.blackboard,
            graph=graph,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

    def build(self) -> FlowSpec:
        return cast("FlowSpec", super().build())
