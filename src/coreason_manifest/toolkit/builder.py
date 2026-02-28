# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Literal, Self, cast

from coreason_manifest.core.compute.reasoning import (
    AdversarialConfig,
    FastPath,
    GapScanConfig,
    ReasoningConfig,
    ReviewStrategy,
    StandardReasoning,
)
from coreason_manifest.core.oversight.governance import (
    CircuitBreaker,
    ComputeLimits,
    DataLimits,
    FinancialLimits,
    Governance,
    OperationalPolicy,
)
from coreason_manifest.core.oversight.intervention import EscalationCriteria
from coreason_manifest.core.oversight.resilience import (
    ErrorDomain,
    ErrorHandler,
    EscalationStrategy,
    FallbackStrategy,
    RecoveryStrategy,
    ResilienceConfig,
    RetryStrategy,
    SupervisionPolicy,
)
from coreason_manifest.core.primitives.types import RiskLevel
from coreason_manifest.core.rebuild import rebuild_manifest
from coreason_manifest.core.state.memory import (
    ConsolidationStrategy,
    EpisodicMemoryConfig,
    MemorySubsystem,
    ProceduralMemoryConfig,
    SemanticMemoryConfig,
    WorkingMemoryConfig,
)
from coreason_manifest.core.state.tools import ToolPack
from coreason_manifest.core.workflow.flow import (
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
)
from coreason_manifest.core.workflow.nodes import AgentNode, CognitiveProfile, HumanNode, InspectorNode
from coreason_manifest.toolkit.validator import validate_flow


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
    """Fluent API to construct AgentNodes.

    This builder simplifies the creation of `AgentNode` objects by providing
    methods to configure identity, reasoning, tools, resilience, and operational
    policies in a chained manner.

    Attributes:
        agent_id (str): The unique identifier for the agent being built.
    """

    def __init__(self, agent_id: str) -> None:
        """Initializes the AgentBuilder.

        Args:
            agent_id (str): The unique identifier for the agent.
        """
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
        # Meta-Cognition state
        self.review_strategy: str = "none"
        self.adversarial_persona: str | None = None
        self.gap_scan_enabled: bool = False
        self.gap_scan_threshold: float = 0.8
        self.max_revisions: int = 1

    def with_meta_cognition(
        self,
        review_strategy: str = "none",
        adversarial_persona: str | None = None,
        gap_scan_enabled: bool = False,
        gap_scan_threshold: float = 0.8,
        max_revisions: int = 1,
    ) -> "AgentBuilder":
        """Configures meta-cognitive features for the agent.

        Args:
            review_strategy (str): The review strategy to use. Defaults to "none".
            adversarial_persona (str | None): The persona for adversarial review.
            gap_scan_enabled (bool): Whether gap scanning is enabled. Defaults to False.
            gap_scan_threshold (float): The threshold for gap scanning. Defaults to 0.8.
            max_revisions (int): Maximum self-correction loops. Defaults to 1.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
        self.review_strategy = review_strategy
        self.adversarial_persona = adversarial_persona
        self.gap_scan_enabled = gap_scan_enabled
        self.gap_scan_threshold = gap_scan_threshold
        self.max_revisions = max_revisions
        return self

    def with_identity(self, role: str, persona: str) -> "AgentBuilder":
        """Configures the agent's identity.

        Args:
            role (str): The role of the agent (e.g., "Analyst").
            persona (str): The persona description (e.g., "You are a helpful assistant...").

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
        self.role = role
        self.persona = persona
        return self

    def with_reasoning(self, model: str, thoughts_max: int = 5, min_confidence: float = 0.7) -> "AgentBuilder":
        """Configures standard Chain of Thought (CoT) reasoning.

        Args:
            model (str): The model to use for reasoning.
            thoughts_max (int): Maximum number of thought steps. Defaults to 5.
            min_confidence (float): Minimum confidence threshold. Defaults to 0.7.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
        self.reasoning = StandardReasoning(model=model, thoughts_max=thoughts_max, min_confidence=min_confidence)
        return self

    def with_fast_path(self, model: str, timeout_ms: int = 1000, caching: bool = True) -> "AgentBuilder":
        """Configures the fast path (System 1) reasoning.

        Args:
            model (str): The model to use for fast path execution.
            timeout_ms (int): Timeout in milliseconds. Defaults to 1000.
            caching (bool): Whether to enable caching. Defaults to True.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
        self.fast_path = FastPath(model=model, timeout_ms=timeout_ms, caching=caching)
        return self

    def with_tools(self, tools: list[str]) -> "AgentBuilder":
        """Adds a list of tools to the agent.

        Args:
            tools (list[str]): A list of tool names/identifiers.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
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
        """Configures the resilience strategy for the agent.

        Args:
            retries (int): Maximum number of retries.
            strategy (str): The resilience strategy ("retry", "fallback", or "escalate").
                Defaults to "escalate".
            backoff (float): Backoff factor for retries. Defaults to 2.0.
            delay (float): Initial delay in seconds. Defaults to 1.0.
            fallback_id (str | None): The ID of the fallback node. Required if strategy is "fallback".
            queue_name (str | None): The queue name for escalation. Defaults to "default_human_queue".

        Returns:
            AgentBuilder: The builder instance for chaining.

        Raises:
            ValueError: If strategy is "fallback" and fallback_id is not provided.
        """
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
        """Configures human steering (escalation) as a supervision policy.

        Args:
            timeout (int): Timeout in seconds for human intervention. Defaults to 300.
            fallback_id (str | None): The ID of the fallback node if escalation times out.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
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
        """Configures operational limits for the agent (financial, compute, data).

        Args:
            max_cost_usd (float | None): Maximum allowed cost in USD.
            max_tokens (int | None): Maximum total tokens allowed.
            fallback_model (str | None): Model to use if budget is depleted.
            max_steps (int | None): Maximum cognitive steps allowed.
            max_execution_time_seconds (int | None): Maximum execution time in seconds.
            max_rows_per_query (int | None): Maximum rows per data query.
            max_payload_bytes (int | None): Maximum payload size in bytes.
            max_search_results (int | None): Maximum number of search results.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
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
        """Adds a local escalation rule to the agent.

        Args:
            condition (str): The condition triggering the escalation.
            role (str): The role responsible for handling the escalation.
            strategy (EscalationStrategy | None): The strategy to execute.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
        self.escalation_rules.append(EscalationCriteria(condition=condition, role=role, strategy=strategy))
        return self

    def with_memory(
        self,
        working_limit: int = 4096,
        enable_paging: bool = False,
        salience_threshold: float | None = None,
        consolidation_interval: int | None = None,
        consolidation_strategy: str = "session_close",
        graph_namespace: str | None = None,
        bitemporal_tracking: bool = False,
        allowed_entity_types: list[str] | None = None,
        skill_library_ref: str | None = None,
    ) -> "AgentBuilder":
        """Configures the memory subsystem for the agent.

        Args:
            working_limit (int): Maximum tokens for working memory. Defaults to 4096.
            enable_paging (bool): Whether to enable active paging. Defaults to False.
            salience_threshold (float | None): Threshold for episodic memory salience.
            consolidation_interval (int | None): Interval for memory consolidation (in turns).
            graph_namespace (str | None): Namespace for semantic memory graph.
            bitemporal_tracking (bool): Whether to enable bitemporal tracking. Defaults to False.
            allowed_entity_types (list[str] | None): Allowed entity types for semantic memory.
            skill_library_ref (str | None): Reference to a skill library for procedural memory.

        Returns:
            AgentBuilder: The builder instance for chaining.
        """
        working = WorkingMemoryConfig(max_tokens=working_limit, enable_active_paging=enable_paging)

        episodic = None
        if salience_threshold is not None:
            episodic = EpisodicMemoryConfig(
                salience_threshold=salience_threshold,
                consolidation_interval_turns=consolidation_interval,
                consolidation_strategy=ConsolidationStrategy(consolidation_strategy),
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
        """Validates configuration and builds the AgentNode.

        Returns:
            AgentNode: The constructed agent node.

        Raises:
            ValueError: If agent identity (role, persona) is not set.
        """
        # Ensure schema is built
        rebuild_manifest()

        if not self.role or not self.persona:
            raise ValueError("Agent identity (role, persona) must be set.")

        reasoning = self.reasoning
        if reasoning is not None:
            gap_scan_config = None
            if self.gap_scan_enabled:
                gap_scan_config = GapScanConfig(
                    enabled=self.gap_scan_enabled, confidence_threshold=self.gap_scan_threshold
                )

            adversarial_config = None
            if self.review_strategy == "adversarial":
                adversarial_config = AdversarialConfig(persona=self.adversarial_persona or "skeptic")

            # Map string to ReviewStrategy Enum
            try:
                review_strategy_enum = ReviewStrategy(self.review_strategy)
            except ValueError:
                review_strategy_enum = ReviewStrategy.NONE

            # Since BaseModel models are immutable (frozen=True), we must use model_copy
            reasoning = reasoning.model_copy(
                update={
                    "review_strategy": review_strategy_enum,
                    "adversarial_config": adversarial_config,
                    "gap_scan": gap_scan_config,
                    "max_revisions": self.max_revisions,
                }
            )

        profile = CognitiveProfile(
            role=self.role,
            persona=self.persona,
            reasoning=reasoning,
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
    """Shared logic for all flow builders to enforce DRY principles.

    This class serves as the foundation for creating different types of flows
    (e.g., LinearFlow, GraphFlow). It manages shared components like metadata,
    profiles, tool packs, supervision templates, and governance policies.

    Attributes:
        metadata (FlowMetadata): Metadata associated with the flow.
        governance (Governance | None): Governance policy for the flow.
    """

    def __init__(self, name: str, version: str, description: str) -> None:
        """Initializes the BaseFlowBuilder.

        Args:
            name (str): The name of the flow.
            version (str): The version of the flow.
            description (str): A description of the flow.
        """
        self.metadata = FlowMetadata(name=name, version=version, description=description, tags=[])
        self._profiles: dict[str, CognitiveProfile] = {}
        self._tool_packs: dict[str, ToolPack] = {}
        self._supervision_templates: dict[str, SupervisionPolicy] = {}
        self.governance: Governance | None = None
        self.status: Literal["draft", "published", "archived"] = "draft"

    def set_status(self, status: Literal["draft", "published", "archived"]) -> Self:
        """Sets the status of the flow.

        Args:
            status (Literal["draft", "published", "archived"]): The status to set.

        Returns:
            Self: The builder instance for chaining.
        """
        self.status = status
        return self

    def define_supervision_template(self, template_id: str, policy: SupervisionPolicy) -> Self:
        """Registers a reusable supervision policy.

        Args:
            template_id (str): The unique ID for the template.
            policy (SupervisionPolicy): The policy definition.

        Returns:
            Self: The builder instance for chaining.
        """
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
        """Registers a reusable profile definition.

        Args:
            profile_id (str): The unique ID for the profile.
            role (str): The role associated with the profile.
            persona (str): The persona description.
            reasoning (ReasoningConfig | None): Optional reasoning configuration.
            fast_path (FastPath | None): Optional fast path configuration.

        Returns:
            Self: The builder instance for chaining.
        """
        self._profiles[profile_id] = CognitiveProfile(
            role=role, persona=persona, reasoning=reasoning, fast_path=fast_path
        )
        return self

    def add_tool_pack(self, pack: ToolPack) -> Self:
        """Adds a tool pack to the flow.

        Args:
            pack (ToolPack): The tool pack to add.

        Returns:
            Self: The builder instance for chaining.
        """
        self._tool_packs[pack.namespace] = pack
        return self

    def set_governance(self, gov: Governance) -> Self:
        """Sets the governance policy.

        Args:
            gov (Governance): The governance policy object.

        Returns:
            Self: The builder instance for chaining.
        """
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
        """Configures global operational limits (Financial, Data, Compute).

        Args:
            max_cost_usd (float | None): Maximum allowed cost in USD.
            max_tokens (int | None): Maximum total tokens allowed.
            fallback_model (str | None): Model to use if budget is depleted.
            max_steps (int | None): Maximum cognitive steps allowed.
            max_execution_time_seconds (int | None): Maximum execution time in seconds.
            max_concurrent_agents (int | None): Maximum number of concurrent agents.
            max_rows_per_query (int | None): Maximum rows per data query.
            max_payload_bytes (int | None): Maximum payload size in bytes.
            max_search_results (int | None): Maximum number of search results.

        Returns:
            Self: The builder instance for chaining.
        """
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
        """Sets the circuit breaker policy.

        Args:
            error_threshold (int): The number of errors to trigger the circuit breaker.
            reset_timeout (int): The timeout in seconds before resetting.
            fallback_node (str | None): The ID of the fallback node.

        Returns:
            Self: The builder instance for chaining.
        """
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
        """Registers a node to the flow. Shared validation logic."""
        if self.governance and self.governance.max_risk_level and isinstance(node, AgentNode):
            max_risk = self.governance.max_risk_level.weight
            available_tools = {}
            for pack in self._tool_packs.values():
                for tool in pack.tools:
                    available_tools[tool.name] = tool.risk_level.weight

            for tool_name in node.tools:
                # Assume a tool is CRITICAL if its definition isn't currently loaded
                tool_risk = available_tools.get(tool_name, RiskLevel.CRITICAL.weight)
                if tool_risk > max_risk:
                    raise ValueError(f"Tool '{tool_name}' exceeds the maximum allowed risk level for this flow.")

    def add_agent_ref(self, node_id: str, profile_id: str, tools: list[str] | None = None) -> Self:
        """Adds a node that points to a registered profile.

        Args:
            node_id (str): The unique identifier for the new node.
            profile_id (str): The ID of the registered profile to use.
            tools (list[str] | None): Optional list of tools for the agent.

        Returns:
            Self: The builder instance for chaining.
        """
        if tools is None:
            tools = []
        node = AgentNode(
            id=node_id,
            metadata={},
            resilience=None,
            type="agent",
            profile=profile_id,
            tools=tools,
            operational_policy=None,
        )
        self._register_node(node)
        return self

    def add_shadow_node(self, node_id: str, prompt: str, shadow_timeout: int = 60) -> Self:
        """Adds a human shadow node to the flow.

        Args:
            node_id (str): The unique identifier for the shadow node.
            prompt (str): The prompt for the human shadow.
            shadow_timeout (int): Timeout in seconds for shadow interaction. Defaults to 60.

        Returns:
            Self: The builder instance for chaining.
        """
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
        """Adds an inspector node to the flow.

        Args:
            node_id (str): The unique identifier for the inspector node.
            target (str): The variable to inspect.
            criteria (str): The criteria for inspection.
            output (str): The variable to store the output.
            pass_threshold (float): The threshold for passing. Defaults to 0.5.

        Returns:
            Self: The builder instance for chaining.
        """
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
        """Constructs and validates the Flow object.

        Returns:
            LinearFlow | GraphFlow: The constructed flow object.

        Raises:
            ValueError: If validation fails.
        """
        # Ensure schema is built
        rebuild_manifest()

        flow = self._create_flow_instance()

        errors = validate_flow(flow)
        if errors:
            # Format structured errors into string for ValueError
            error_msgs = [f"[{e.code}] {e.message}" for e in errors]
            raise ValueError("Validation failed:\n- " + "\n- ".join(error_msgs))

        return flow


class NewLinearFlow(BaseFlowBuilder):
    """Fluent API to construct LinearFlows programmatically.

    LinearFlows represent a sequence of steps executed in order.
    """

    def __init__(self, name: str, version: str = "0.1.0", description: str = "") -> None:
        """Initializes the NewLinearFlow builder.

        Args:
            name (str): The name of the flow.
            version (str): The version of the flow. Defaults to "0.1.0".
            description (str): A description of the flow. Defaults to "".
        """
        super().__init__(name, version, description)
        self.steps: list[AnyNode] = []

    def _register_node(self, node: AnyNode) -> None:
        super()._register_node(node)
        self.steps.append(node)

    def add_step(self, node: AnyNode) -> "NewLinearFlow":
        """Appends a node to the sequence.

        Args:
            node (AnyNode): The node to add.

        Returns:
            NewLinearFlow: The builder instance for chaining.
        """
        self.steps.append(node)
        return self

    def add_agent(self, agent: AgentNode) -> "NewLinearFlow":
        """Appends an agent node to the sequence.

        Args:
            agent (AgentNode): The agent node to add.

        Returns:
            NewLinearFlow: The builder instance for chaining.
        """
        self.steps.append(agent)
        return self

    def _create_flow_instance(self) -> LinearFlow:
        return LinearFlow(
            kind="LinearFlow",
            status=self.status,
            metadata=self.metadata,
            steps=self.steps,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

    def build(self) -> LinearFlow:
        """Constructs and validates the LinearFlow object.

        Returns:
            LinearFlow: The constructed linear flow.
        """
        # Override return type hint for better IDE support, but reuse base implementation
        return cast("LinearFlow", super().build())


class NewGraphFlow(BaseFlowBuilder):
    """Fluent API to construct GraphFlows programmatically.

    GraphFlows represent a graph of nodes connected by edges, allowing for
    complex branching and looping logic.
    """

    def __init__(self, name: str, version: str = "0.1.0", description: str = "") -> None:
        """Initializes the NewGraphFlow builder.

        Args:
            name (str): The name of the flow.
            version (str): The version of the flow. Defaults to "0.1.0".
            description (str): A description of the flow. Defaults to "".
        """
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
        super()._register_node(node)
        self._nodes[node.id] = node

    def set_entry_point(self, node_id: str) -> "NewGraphFlow":
        """Sets the explicit entry point for the graph.

        Args:
            node_id (str): The ID of the entry point node.

        Returns:
            NewGraphFlow: The builder instance for chaining.
        """
        self._entry_point = node_id
        return self

    def add_node(self, node: AnyNode) -> "NewGraphFlow":
        """Adds a node to the graph.

        Args:
            node (AnyNode): The node to add.

        Returns:
            NewGraphFlow: The builder instance for chaining.
        """
        self._nodes[node.id] = node
        return self

    def add_agent(self, agent: AgentNode) -> "NewGraphFlow":
        """Adds an agent node to the graph.

        Args:
            agent (AgentNode): The agent node to add.

        Returns:
            NewGraphFlow: The builder instance for chaining.
        """
        self._nodes[agent.id] = agent
        return self

    def connect(self, source: str, target: str, condition: str | None = None) -> "NewGraphFlow":
        """Adds an edge to the graph.

        Args:
            source (str): The ID of the source node.
            target (str): The ID of the target node.
            condition (str | None): Optional condition for traversing the edge.

        Returns:
            NewGraphFlow: The builder instance for chaining.
        """
        self._edges.append(Edge(from_node=source, to_node=target, condition=condition))
        return self

    def set_interface(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> "NewGraphFlow":
        """Defines the Input/Output contract for the Flow.

        Args:
            inputs (dict[str, Any]): JSON schema for inputs.
            outputs (dict[str, Any]): JSON schema for outputs.

        Returns:
            NewGraphFlow: The builder instance for chaining.
        """
        self.interface = FlowInterface(
            inputs=DataSchema(json_schema=inputs),
            outputs=DataSchema(json_schema=outputs),
        )
        return self

    def set_blackboard(self, variables: dict[str, dict[str, Any]], persistence: Any | None = None) -> "NewGraphFlow":
        """Configures the shared memory blackboard.

        Args:
            variables (dict[str, dict[str, Any]]): Blackboard variable definitions.
            persistence (Any | None): Optional persistence config mapping. Defaults to None.

        Returns:
            NewGraphFlow: The builder instance for chaining.
        """
        # Note: If boolean passed historically, ignore or map to default. We set to None for simplicity if False
        if persistence is False:
            persistence = None
        self.blackboard = Blackboard(variables=variables, persistence=persistence)
        return self

    def _create_flow_instance(self) -> GraphFlow:
        # Determine entry point
        ep = self._entry_point
        if not ep:
            ep = next(iter(self._nodes.keys())) if self._nodes else "missing_entry_point"

        graph = Graph(nodes=self._nodes, edges=self._edges, entry_point=ep)

        return GraphFlow(
            kind="GraphFlow",
            status=self.status,
            metadata=self.metadata,
            interface=self.interface,
            blackboard=self.blackboard,
            graph=graph,
            definitions=self._build_definitions(),
            governance=self.governance,
        )

    def build(self) -> GraphFlow:
        """Constructs and validates the GraphFlow object.

        Returns:
            GraphFlow: The constructed graph flow.
        """
        # Override return type hint
        return cast("GraphFlow", super().build())
