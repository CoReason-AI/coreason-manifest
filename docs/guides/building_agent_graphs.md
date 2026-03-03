# Building Agent Graphs

`coreason_manifest` allows you to construct complex, multi-agent workflows using a Directed Acyclic Graph (DAG) architecture. By defining independent units of execution (`Nodes`) and mapping their data flow (`Edges`), you can build robust and scalable AI systems.

This guide demonstrates how to construct a standard enterprise DAG involving a `RoutingNode`, an `AgentNode`, and a `HumanNode`.

## Understanding the Topology

The `GraphFlow` architecture requires three essential components:

1.  **Nodes:** Independent execution blocks.
2.  **Edges:** The defined transitions between nodes.
3.  **Entry Point:** The starting node for execution.

!!! warning "Strict Cycle Detection"
    `coreason_manifest` employs strict cycle detection at initialization. If your `Edges` create an infinite loop, a `TopologyException` will be raised before execution begins.

## Step 1: Define Your Nodes

Let's imagine a customer support workflow. The incoming request is analyzed, routed to a specialized agent, and then reviewed by a human if necessary.

```python
from coreason_manifest.core.workflow.nodes import AgentNode, HumanNode, RoutingNode
from coreason_manifest.core.workflow.topology import ConditionalEdge

# 1. Routing Node: Analyzes intent
router = RoutingNode(
    id="intent_router",
    system_prompt="Analyze the request and return 'billing' or 'technical'."
)

# 2. Agent Node: Handles billing inquiries
billing_agent = AgentNode(
    id="billing_specialist",
    system_prompt="You are a billing specialist. Resolve the payment issue."
)

# 3. Agent Node: Handles technical inquiries
tech_agent = AgentNode(
    id="technical_support",
    system_prompt="You are a tech support engineer. Troubleshoot the issue."
)

# 4. Human Node: Approves final resolution
human_review = HumanNode(
    id="manager_approval",
    instruction="Review the proposed resolution before sending to the customer."
)
```

!!! note "Dynamic Execution Constraints"
    When using `AgentNode`, understand that it acts as a dynamic execution boundary. The output of an `AgentNode` is non-deterministic, emphasizing the importance of `Governance` layers.

## Step 2: Establish Edges

Edges define the flow of execution and data. `ConditionalEdge` allows you to route execution based on the output of a prior node.

```python
from coreason_manifest.core.workflow.topology import Edge, ConditionalEdge

# Route from intent analyzer based on output
routing_edge = ConditionalEdge(
    source="intent_router",
    condition_map={
        "billing": "billing_specialist",
        "technical": "technical_support"
    },
    default_target="human_approval" # Fallback if unrecognized
)

# Both agents route to the human review step
billing_to_human = Edge(source="billing_specialist", target="manager_approval")
tech_to_human = Edge(source="technical_support", target="manager_approval")

edges = [routing_edge, billing_to_human, tech_to_human]
```

## Step 3: Construct the GraphFlow

With your nodes and edges defined, instantiate the `GraphFlow`. Pydantic V2 validation immediately kicks in to verify your topology.

```python
from coreason_manifest.core.workflow.flow import GraphFlow

support_flow = GraphFlow(
    id="customer_support_pipeline",
    nodes=[router, billing_agent, tech_agent, human_review],
    edges=edges,
    entry_point="intent_router"
)

# The support_flow is now validated and ready for execution.
```

## Next Steps

Now that your topology is established, consider implementing strict operational constraints around the `AgentNode` components. Proceed to [Enforcing Governance](enforcing_governance.md) to learn more.