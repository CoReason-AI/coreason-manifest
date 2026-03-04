from typing import Any

from coreason_manifest.presentation.scivis.scientific_vis import (
    HierarchicalBlueprint,
    SciVisIntent,
    VisualCriticFeedback,
)
from coreason_manifest.workflow.flow import Blackboard, Edge, Graph, GraphFlow
from coreason_manifest.workflow.nodes import AgentNode, PlannerNode, VisualInspectorNode


class SciVisDraftingBlackboard(Blackboard):
    intent: SciVisIntent
    current_blueprint: HierarchicalBlueprint | None = None
    critic_feedback: VisualCriticFeedback | None = None
    iteration_count: int = 0


class SciVisPlannerNode(PlannerNode):
    pass


class SciVisLayoutAgentNode(AgentNode):
    pass


class SciVisCriticNode(VisualInspectorNode):
    pass


class SciVisDraftingFlow(GraphFlow):
    def __init__(self, **data: Any) -> None:
        planner = SciVisPlannerNode(
            id="planner",
            goal="Analyze intent and setup prompt strategy",
            output_schema={"type": "object"},
        )
        drafter = SciVisLayoutAgentNode(id="drafter", profile="scivis_drafter", operational_policy=None)
        critic = SciVisCriticNode(
            id="critic",
            target_variable="current_blueprint",
            criteria="Check for overlapping nodes or LaTeX errors",
            output_variable="critic_feedback",
            target_artifact_key="blueprint_image",
        )

        edges = [
            Edge(from_node="planner", to_node="drafter"),
            Edge(from_node="drafter", to_node="critic"),
        ]

        graph = Graph(
            nodes={"planner": planner, "drafter": drafter, "critic": critic},
            edges=edges,
            entry_point="planner",
        )

        if "metadata" not in data:
            data["metadata"] = {"name": "SciVisDraftingTopology", "version": "1.0.0"}
        if "interface" not in data:
            data["interface"] = {}

        data["graph"] = graph

        super().__init__(**data)
