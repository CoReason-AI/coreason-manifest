# Coreason Agent Manifest (CAM) V2

The **Coreason Agent Manifest (CAM)**, also known as **Manifest V2**, is the "Human-Centric" Canonical YAML format designed for defining Agents and Recipes in the Coreason ecosystem. It serves as the primary interface for developers and the Visual Builder.

> **Note:** The CAM is designed for ease of authoring. At runtime, the Coreason Engine compiles this YAML into strict, machine-optimized Pydantic models. For details on the runtime format, see the [Runtime Agent Definition (V1)](runtime_agent_definition.md) and [Runtime Recipe Definition (V1)](runtime_recipe_definition.md).

## Root Object (`ManifestV2`)

The root of the document follows a "Kubernetes-style" header structure.

```yaml
apiVersion: coreason.ai/v2
kind: Recipe  # or 'Agent'
metadata:
  name: "My Workflow"
  version: "1.0.0"
  x-design:
    color: "#4A90E2"
interface:
  inputs: ...
  outputs: ...
state:
  schema: ...
policy:
  max_retries: 3
definitions:
  ...
workflow:
  start: "step1"
  steps: ...
```

### Top-Level Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `apiVersion` | `Literal["coreason.ai/v2"]` | Must be `coreason.ai/v2`. |
| `kind` | `Literal["Recipe", "Agent"]` | The type of asset being defined. |
| `metadata` | `ManifestMetadata` | Metadata including name, version, and design info. |
| `interface` | `InterfaceDefinition` | Defines the Input/Output contract. |
| `state` | `StateDefinition` | Defines the internal memory schema. |
| `policy` | `PolicyDefinition` | Governance and execution policy. |
| `definitions` | `Dict[str, Any]` | Reusable component definitions (Tools, Agents, etc.). |
| `workflow` | `Workflow` | The main execution topology. |

## 1. Definitions Section

The `definitions` section is a polymorphic key-value map where you can define reusable components. These components can then be referenced by ID within the workflow.

### Tool Definition (`ToolDefinition`)
*   `type`: `tool`
*   `id`: Unique identifier.
*   `name`: Human-readable name.
*   `uri`: The MCP endpoint URI.
*   `risk_level`: `safe`, `standard`, or `critical`.

### Agent Definition (`AgentDefinition`)
*   `type`: `agent`
*   `id`: Unique identifier.
*   `name`: Agent name.
*   `role`: The persona/job title.
*   `goal`: The primary objective.
*   `backstory`: Detailed instructions or persona background.
*   `tools`: List of tool IDs (referencing other definitions).
*   `model`: LLM identifier (e.g., `gpt-4`).

### Generic Definition
Fallback for loose dictionaries or references (`$ref`) that haven't been resolved yet.

#### Example Definitions Block
```yaml
definitions:
  # Define a Tool
  search_tool:
    type: tool
    id: search
    name: Google Search
    uri: mcp://google-search
    risk_level: safe

  # Define a Native Agent
  writer_agent:
    type: agent
    id: writer
    name: Content Writer
    role: Senior Editor
    goal: Summarize research into a blog post.
    backstory: You are an expert editor with a focus on clarity.
    tools: ["search"] # References the tool ID above
    model: "gpt-4"
```

## 2. Interface (`InterfaceDefinition`)

Defines the contract for interacting with the workflow.

| Field | Type | Description |
| :--- | :--- | :--- |
| `inputs` | `Dict[str, Any]` | JSON Schema definitions for arguments. |
| `outputs` | `Dict[str, Any]` | JSON Schema definitions for return values. |

**Example:**
```yaml
interface:
  inputs:
    topic:
      type: string
      description: "The research topic."
  outputs:
    summary:
      type: string
      description: "The final summary."
```

## 3. State (`StateDefinition`)

Defines the shared memory available to the workflow.

| Field | Type | Description |
| :--- | :--- | :--- |
| `schema` | `Dict[str, Any]` | JSON Schema of the keys available in the shared memory. |
| `backend` | `Optional[str]` | Backend storage type (e.g., `redis`, `memory`). |

**Example:**
```yaml
state:
  schema:
    messages:
      type: array
      items:
        type: string
  backend: "redis"
```

## 4. Policy (`PolicyDefinition`)

Defines execution limits and governance rules.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_steps` | `Optional[int]` | `None` | Execution limit on number of steps. |
| `max_retries` | `int` | `3` | Maximum number of retries for failed steps. |
| `timeout` | `Optional[int]` | `None` | Timeout in seconds. |
| `human_in_the_loop` | `bool` | `False` | Whether to require human approval. |

## 5. Workflow (`Workflow`)

Defines the steps and their flow. Unlike V1, which uses an explicit Edge List, V2 uses an implicit "Linked List" via the `next` field in each step.

| Field | Type | Description |
| :--- | :--- | :--- |
| `start` | `str` | The ID of the starting step. |
| `steps` | `Dict[str, Step]` | Dictionary of all steps indexed by ID. |

### Step Types

All steps include `id`, `inputs`, and `next` (except `switch`).

#### Agent Step (`type: agent`)
Executes an AI Agent.
- `agent`: Reference to an Agent definition (by ID or name).
- `system_prompt`: Optional override.

#### Logic Step (`type: logic`)
Executes Python code.
- `code`: The Python code to execute.

#### Switch Step (`type: switch`)
Routes execution based on conditions.
- `cases`: Dictionary of condition expressions to Step IDs.
- `default`: Default Step ID if no cases match.
- *Note: Does not use `next`.*

#### Council Step (`type: council`)
Involves multiple voters/agents.
- `voters`: List of Agent IDs.
- `strategy`: Voting strategy (e.g., `consensus`).

## Complete Example Manifest

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Research Workflow"
interface:
  inputs:
    query:
      type: string
policy:
  max_retries: 5
definitions:
  google_search:
    type: tool
    id: google_search
    uri: mcp://google
    risk_level: safe

  researcher:
    type: agent
    id: researcher
    role: Researcher
    goal: Find information
    tools: ["google_search"]
    model: "gpt-4"

workflow:
  start: "search"
  steps:
    search:
      type: agent
      id: "search"
      agent: "researcher"
      next: "summarize"

    summarize:
      type: agent
      id: "summarize"
      agent: "gpt-4-turbo" # Can reference model directly if simple
      system_prompt: "Summarize the findings."
```
