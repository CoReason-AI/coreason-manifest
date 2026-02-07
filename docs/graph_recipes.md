# Graph Recipes (Work Package JJ)

The **Recipe** system is the "Brain" of the Coreason execution model. While `AgentDefinition` describes *what* an agent can do (its tools and capabilities), a `RecipeDefinition` describes *how* tasks are orchestrated.

Recipes upgrade the system from simple linear lists of steps to executing complex, non-linear **Directed Cyclic Graphs (DCGs)**. This enables:

*   **Loops:** "If quality < 50%, critique and revise."
*   **Branching:** "If legal query, route to Legal Agent; else route to General Agent."
*   **Human-in-the-Loop:** "Pause and wait for Manager Approval."

## Architecture

A `RecipeDefinition` is a specialized Manifest type (`kind: Recipe`) that contains a `GraphTopology`.

### Graph Topology

The topology consists of:
*   **Nodes**: Units of work (Agents, Humans, Routers).
*   **Edges**: Directed connections defining the flow of control.
*   **Entry Point**: The ID of the node where execution begins.

The system enforces strict **Graph Integrity**:
*   The `entry_point` must exist in the node list.
*   All edges must connect valid source and target nodes (no dangling pointers).
*   Cycles (loops) are explicitly allowed and supported.

## Node Types

Nodes are polymorphic and identified by their `type` field.

### 1. Agent Node (`type: agent`)
Executes an AI Agent.

```yaml
type: agent
id: "research-step"
agent_ref: "researcher-agent-v1"
system_prompt_override: "Focus on recent news."
inputs_map:
  topic: "user_query"
```

### 2. Human Node (`type: human`)
Pauses execution and waits for external human intervention.

```yaml
type: human
id: "manager-approval"
prompt: "Please review the draft."
timeout_seconds: 3600
required_role: "editor"
```

### 3. Router Node (`type: router`)
Evaluates a variable and routes execution to different paths.

```yaml
type: router
id: "quality-gate"
input_key: "score"
routes:
  high: "publish-step"
  low: "revise-step"
default_route: "manual-review"
```

## Example Recipe

Here is a complete example of a Recipe that includes a loop and human approval.

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Blog Post Workflow"
topology:
  entry_point: "draft"
  nodes:
    - type: agent
      id: "draft"
      agent_ref: "writer-agent"

    - type: agent
      id: "critique"
      agent_ref: "editor-agent"

    - type: router
      id: "check-quality"
      input_key: "score"
      routes:
        pass: "human-approve"
      default_route: "draft"  # Loop back to draft if quality fails

    - type: human
      id: "human-approve"
      prompt: "Approve for publication?"

    - type: agent
      id: "publish"
      agent_ref: "publisher-agent"

  edges:
    - source: "draft"
      target: "critique"
    - source: "critique"
      target: "check-quality"
    # Router logic handles the next steps dynamically, but edges can visualize the flow
    - source: "check-quality"
      target: "draft"
      condition: "default (fail)"
    - source: "check-quality"
      target: "human-approve"
      condition: "pass"
    - source: "human-approve"
      target: "publish"
```

## Validation

The `coreason-manifest` library includes strict Pydantic validation for Recipes.

```python
from coreason_manifest import RecipeDefinition, GraphTopology

# This will raise ValidationError if integrity checks fail
recipe = RecipeDefinition.model_validate(data)
```
