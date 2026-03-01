from coreason_manifest.core.domains.mcp_contracts import MCPOperationSequence
from coreason_manifest.core.domains.scientific_vis import HierarchicalBlueprint, SciVisIntent
from coreason_manifest.core.domains.scivis_spatial import SpatialLayoutBlueprint
from coreason_manifest.core.domains.scivis_style import DesignSystemConfig
from coreason_manifest.core.oversight.resilience import EscalationStrategy
from coreason_manifest.core.workflow.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.core.workflow.nodes import (
    AgentNode,
    CognitiveProfile,
    HumanNode,
    PlannerNode,
    SteeringConfig,
    SwitchNode,
)
from coreason_manifest.core.workflow.nodes.visual_oversight import VisBenchRubricConfig, VisualInspectorNode


def get_sota_scivis_topology() -> GraphFlow:
    """Creates the SOTA 2026 scientific illustration topology."""

    # Node 1: semantic_parser
    semantic_parser = PlannerNode(
        id="semantic_parser",
        goal="Parses text to hierarchical blueprint",
        output_schema=HierarchicalBlueprint.model_json_schema(),
    )

    # Node 2: layout_agent
    layout_agent = AgentNode(
        id="layout_agent",
        profile=CognitiveProfile(
            role="Layout Designer",
            persona="Drafts relative spatial constraints and layouts (AST) based on the academic design system.",
        ),
        output_schema=SpatialLayoutBlueprint.model_json_schema(),
        operational_policy=None,
    )

    # Node 3: visual_critic
    visual_critic = VisualInspectorNode(
        id="visual_critic",
        target_variable="layout",
        criteria="Applies VisBench rubrics to layout",
        output_variable="critique_result",
        target_artifact_key="rendered_layout_svg",
        rubrics=VisBenchRubricConfig(
            check_alignment=True,
            check_text_readability=True,
            check_spatial_overlap=True,
            check_hallucinations=True,
        ),
    )

    # Node 4: critique_router
    critique_router = SwitchNode(
        id="critique_router",
        variable="critique_result",
        cases={"rejected": "layout_agent"},
        default="human_expert_review",
    )

    # Node 4.5: human_expert_review
    human_expert_review = HumanNode(
        id="human_expert_review",
        prompt="Review the logical HierarchicalBlueprint and spatial SpatialLayoutBlueprint before rendering.",
        options=["approve_to_render", "reject_to_layout", "reject_to_planner"],
        escalation=EscalationStrategy(
            type="escalate",
            queue_name="human_review",
            notification_level="info",
            timeout_seconds=3600,
        ),
        steering_config=SteeringConfig(
            allow_variable_mutation=False,
        ),
    )

    # Node 5: final_renderer
    final_renderer = AgentNode(
        id="final_renderer",
        profile=CognitiveProfile(
            role="Renderer",
            persona="Executes atomic MCP tool transactions on a headless canvas to render the final artifact.",
        ),
        output_schema=MCPOperationSequence.model_json_schema(),
        operational_policy=None,
    )

    # Wire edges for Directed Cyclic Graph (DCG)
    edges = [
        Edge(from_node="semantic_parser", to_node="layout_agent"),
        Edge(from_node="layout_agent", to_node="visual_critic"),
        Edge(from_node="visual_critic", to_node="critique_router"),
        Edge(from_node="critique_router", to_node="layout_agent", condition="rejected"),
        Edge(from_node="critique_router", to_node="human_expert_review", condition="approved"),
        Edge(from_node="human_expert_review", to_node="final_renderer", condition="approve_to_render"),
        Edge(from_node="human_expert_review", to_node="layout_agent", condition="reject_to_layout"),
        Edge(from_node="human_expert_review", to_node="semantic_parser", condition="reject_to_planner"),
    ]

    nodes_dict = {
        semantic_parser.id: semantic_parser,
        layout_agent.id: layout_agent,
        visual_critic.id: visual_critic,
        critique_router.id: critique_router,
        human_expert_review.id: human_expert_review,
        final_renderer.id: final_renderer,
    }

    # Bypass Graph model_validator to allow Directed Cyclic Graph (DCG)
    graph = Graph.model_construct(
        nodes=nodes_dict,
        edges=edges,
        entry_point="semantic_parser",
    )

    return GraphFlow.model_construct(
        annotations={"id": "sota_scientific_illustration_v1"},
        metadata=FlowMetadata(
            name="SOTA Sci-Vis Flow",
            version="1.0.0",
            description="2026 SOTA Topology for Scientific Visualization",
        ),
        interface=FlowInterface(
            inputs={
                "intent": SciVisIntent.model_json_schema(),
                "style_profile": DesignSystemConfig.model_json_schema(),
            }
        ),
        graph=graph,
        type="graph",
        kind="GraphFlow",
        status="draft",
        pre_flight_constraints=[],
    )
