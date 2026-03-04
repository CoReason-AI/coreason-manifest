from typing import Literal

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.workflow.nodes.base import Node


class HybridMCTSEvolutionConfig(CoreasonModel):
    """
    Configuration for blending Monte Carlo Tree Search (MCTS) with genetic mutations
    to explore reasoning paths in a 2026 Evolutionary MCTS architecture.
    """
    population_limit: int = Field(
        ...,
        gt=0,
        description="Maximum concurrent reasoning variants. Must be strictly greater than 0."
    )
    mcts_lookahead_depth: int = Field(
        ...,
        description="How many reasoning steps into the future the tree search should simulate before rolling back."
    )
    exploration_weight_c_puct: float = Field(
        ...,
        description="The UCB1 constant balancing exploration vs. exploitation (typically around 1.0 - 1.4)."
    )
    crossover_strategy: Literal["semantic_blend", "tool_swap", "prompt_splice"] = Field(
        ...,
        description="How two successful reasoning paths are merged."
    )


class CostAwareFitnessMetric(CoreasonModel):
    """
    Extends standard accuracy metrics to penalize heavy test-time compute.
    This ensures the evolutionary loop selects for efficiency, not just raw intelligence
    within the 2026 Evolutionary MCTS architecture.
    """
    base_reward_metric_uri: str = Field(
        ...,
        description="Pointer to the primary accuracy evaluator."
    )
    token_bloat_penalty: float = Field(
        ...,
        le=0.0,
        description="Negative weight applied per 1k tokens generated."
    )
    latency_penalty_ms: float = Field(
        ...,
        le=0.0,
        description="Negative weight applied for slow execution."
    )
    max_acceptable_cost_usd: float = Field(
        ...,
        description="Hard ceiling constraint per evolutionary run."
    )


class ShadowPopulationConfig(CoreasonModel):
    """
    Dictates how a deployed agent maintains a silent, background population of variants
    in a 2026 Evolutionary MCTS architecture.
    """
    background_mutation_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The percentage chance of an idle variant mutating its instructions (must be between 0.0 and 1.0)."
    )
    hot_swap_threshold: float = Field(
        ...,
        description="The delta in fitness score required for a shadow variant to replace the primary production agent."
    )
    telemetry_feedback_sync: bool = Field(
        ...,
        description="Whether the shadow variants use real-time user telemetry for their fitness evaluations."
    )


class EvolutionaryReasoningTopology(Node):
    """
    The primary node definition that ties 2026 Evolutionary MCTS concepts
    together into the workflow graph.
    """
    type: Literal["evolutionary_reasoning"] = Field(
        "evolutionary_reasoning",
        description="The type of the node."
    )
    target_intent: str = Field(
        ...,
        description="The complex problem this node must solve."
    )
    mcts_config: HybridMCTSEvolutionConfig = Field(
        ...,
        description="Configuration for blending MCTS with genetic mutations."
    )
    fitness_evaluator: CostAwareFitnessMetric = Field(
        ...,
        description="Metric that extends standard accuracy with compute cost penalties."
    )
    shadow_deployment: ShadowPopulationConfig | None = Field(
        None,
        description="Optional configuration for a background shadow variant population."
    )
