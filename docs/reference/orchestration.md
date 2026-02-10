# Orchestration

## Overview
This module controls the flow of execution within an agentic workflow, defining how nodes ([agents](../reference/agents.md), routers, humans) are connected and how data flows between them.

## Application Pattern
This example demonstrates how to wire a [GraphTopology][coreason_manifest.spec.v2.recipe.GraphTopology] with a simple feedback loop, where an [AgentNode][coreason_manifest.spec.v2.recipe.AgentNode]'s output is evaluated and potentially routed back for refinement.

```python
# Example: Instantiating a GraphTopology with a Loop
from coreason_manifest.spec.v2.recipe import (
    GraphTopology,
    AgentNode,
    EvaluatorNode,
    GraphEdge
)

# Define the Agent Node (The Doer)
# Refers to an AgentDefinition in 'agents.md'
agent_node = AgentNode(
    id="step_1_generate",
    agent_ref="agent-writer-v1"
)

# Define the Evaluator Node (The Checker)
evaluator_node = EvaluatorNode(
    id="step_2_evaluate",
    target_variable="step_1_generate.output",
    evaluator_agent_ref="agent-editor-v1",
    evaluation_profile="profile-grammar-check",
    pass_threshold=0.8,
    max_refinements=3,
    pass_route="end",
    fail_route="step_1_generate",  # Loop back on failure
    feedback_variable="editor_feedback"
)

# Define the Topology
topology = GraphTopology(
    entry_point="step_1_generate",
    nodes=[agent_node, evaluator_node],
    edges=[
        GraphEdge(source="step_1_generate", target="step_2_evaluate"),
        # The loops are implicit in the EvaluatorNode's pass/fail routes,
        # but can also be explicit edges for visualization tools.
        GraphEdge(source="step_2_evaluate", target="step_1_generate", condition="needs_revision")
    ]
)
```

## API Reference

::: coreason_manifest.spec.v2.recipe.RecipeDefinition

::: coreason_manifest.spec.v2.recipe.GraphTopology

::: coreason_manifest.spec.v2.recipe.AgentNode
