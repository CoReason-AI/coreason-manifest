# Graph Recipes (Work Package JJ)

The **Recipe** system is the "Brain" of the Coreason execution model. While `AgentDefinition` describes *what* an agent can do (its tools and capabilities), a `RecipeDefinition` describes *how* tasks are orchestrated.

Recipes upgrade the system from simple linear lists of steps to executing complex, non-linear **Directed Cyclic Graphs (DCGs)**. This enables:

*   **Loops:** "If quality < 50%, critique and revise."
*   **Branching:** "If legal query, route to Legal Agent; else route to General Agent."
*   **Human-in-the-Loop:** "Pause and wait for Manager Approval."

## Architecture

A `RecipeDefinition` is a specialized Manifest type (`kind: Recipe`) that contains a `GraphTopology` along with other key components:

### 1. The Interface Layer (Contract)

Defines the input/output contract for the Recipe using JSON Schema.

```yaml
interface:
  inputs:
    topic:
      type: string
  outputs:
    summary:
      type: string
```

### 2. The State Layer (Memory)

Defines the shared memory (Blackboard) schema and persistence strategy.

```yaml
state:
  properties:
    draft_content:
      type: string
    vote_count:
      type: integer
  persistence: "redis" # Options: ephemeral, redis, postgres
```

### 3. The Policy Layer (Governance)

Sets execution limits and error handling strategies.

```yaml
policy:
  max_retries: 5
  timeout_seconds: 3600
  execution_mode: "parallel" # Options: sequential, parallel
```

### 4. Graph Topology

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

Here is a complete example of a Recipe that includes a loop, human approval, state, and policy.

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Blog Post Workflow"

interface:
  inputs:
    topic: {type: string}
  outputs:
    final_post: {type: string}

state:
  properties:
    draft: {type: string}
    status: {type: string}
  persistence: "ephemeral"

policy:
  max_retries: 2
  timeout_seconds: 600

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

## Advanced Patterns

### Self-Refining Loop (Recursive)

A common pattern is an agent that critiques and improves its own work until a quality threshold is met.

```yaml
topology:
  entry_point: "generate"
  nodes:
    - type: agent
      id: "generate"
      agent_ref: "coder-agent"
      # Agent takes 'feedback' as input; on first run it might be empty
      inputs_map:
        feedback: "critique_output"

    - type: agent
      id: "evaluate"
      agent_ref: "qa-agent"
      inputs_map:
        code: "generate_output"

    - type: router
      id: "check-score"
      input_key: "quality_score"
      routes:
        pass: "deploy"
      default_route: "generate" # Recursive loop back to start

    - type: agent
      id: "deploy"
      agent_ref: "ops-agent"

  edges:
    - source: "generate"
      target: "evaluate"
    - source: "evaluate"
      target: "check-score"
    - source: "check-score"
      target: "generate"
      condition: "fail (loop)"
    - source: "check-score"
      target: "deploy"
      condition: "pass"
```

## Validation

The `coreason-manifest` library includes strict Pydantic validation for Recipes.

```python
from coreason_manifest import RecipeDefinition, GraphTopology

# This will raise ValidationError if integrity checks fail
recipe = RecipeDefinition.model_validate(data)
```
