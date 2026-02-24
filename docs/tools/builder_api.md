# Developer Tools: The Builder API

Writing a large JSON manifest by hand is error-prone. One typo in a `NodeID` reference can break a 50-node graph.

The `coreason-manifest` package provides a fluent, type-safe Python API (`src/coreason_manifest/builder.py`) to construct valid schemas programmatically. This Builder API guarantees structural validity before you ever export to JSON.

---

## `NewLinearFlow` & `NewGraphFlow`

These helper classes act as the root context for building a workflow. They automatically handle:
1.  **Topology Validation:** Ensuring `entry_point` exists and there are no disconnected islands.
2.  **Type Safety:** Ensuring only valid `AnyNode` objects are added.
3.  **Registry Management:** Automatically registering Profiles and Tool Packs in the `definitions` block.
4.  **Policy Configuration:** Easily setting governance policies like `.set_operational_policy()` and `.set_circuit_breaker()`.

```python
from coreason_manifest.builder import NewGraphFlow, AgentBuilder

# Initialize the Flow
flow_builder = NewGraphFlow("Research Assistant", version="1.0.0")

# Define a reusable profile
flow_builder.define_profile("researcher", role="Analyst", persona="Be concise.")

# Define Topology
flow_builder.set_entry_point("start")
```

---

## `AgentBuilder`

The `AgentBuilder` provides a fluent interface to construct complex `AgentNode` objects without needing to instantiate nested Pydantic models manually.

*   **`with_identity(role, persona)`**: Sets the Cognitive Profile.
*   **`with_reasoning(model, ...)`**: Configures the thinking engine.
*   **`with_resilience(retries, ...)`**: Attaches a supervision policy.

```python
agent = (
    AgentBuilder("step_1")
    .with_identity("Researcher", "Search for facts.")
    .with_reasoning("gpt-4", thoughts_max=3)
    .with_tools(["web_search"])
    .build()  # Returns a validated AgentNode
)

flow_builder.add_agent(agent)
```

---

## Conceptual Example: Building a Graph

Here is how to build a small DAG where a router sends work to either a Researcher or a coder.

```python
# 1. Create Builder
builder = NewGraphFlow("Tech Support Bot")

# 2. Add Nodes
builder.add_node(
    SwitchNode(
        id="router",
        variable="intent",
        cases={"code": "coder", "search": "researcher"},
        default="researcher"
    )
)

builder.add_agent(
    AgentBuilder("coder").with_identity("Dev", "Write code.").build()
)

builder.add_agent(
    AgentBuilder("researcher").with_identity("Analyst", "Search docs.").build()
)

# 3. Connect Edges
builder.connect("router", "coder", condition="intent == 'code'")
builder.connect("router", "researcher", condition="intent == 'search'")

# 4. Export
manifest = builder.build()  # Returns GraphFlow
print(manifest.model_dump_json(indent=2))
```
