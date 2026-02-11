# Orchestration

## Overview
This module defines how to wire a `GraphFlow` with feedback loops, where an `AgentNode`'s output is evaluated and potentially routed back for refinement.

## Graph Example

```python
from coreason_manifest.spec.core.flow import GraphFlow, Graph, Edge, FlowMetadata, FlowInterface
from coreason_manifest.spec.core.nodes import AgentNode, SwitchNode

# Create Nodes (simplified for brevity)
nodes = {
    "agent": AgentNode(...),
    "check": SwitchNode(
        type="switch",
        id="check-quality",
        variable="score",
        cases={">0.9": "publish"},
        default="agent"
    )
}

# Create Edges
edges = [
    Edge(source="agent", target="check"),
    Edge(source="check", target="agent", condition="default"),
    Edge(source="check", target="publish", condition=">0.9")
]

# Create Flow
flow = GraphFlow(
    kind="GraphFlow",
    metadata=FlowMetadata(name="Loop", version="1.0", description="...", tags=[]),
    interface=FlowInterface(inputs={}, outputs={}),
    blackboard=None,
    graph=Graph(nodes=nodes, edges=edges)
)
```

## API Reference

::: coreason_manifest.spec.core.flow.GraphFlow

::: coreason_manifest.spec.core.flow.Graph

::: coreason_manifest.spec.core.flow.Edge

::: coreason_manifest.spec.core.flow.FlowMetadata

::: coreason_manifest.spec.core.flow.FlowInterface
