# Coreason Agent Manifest (CAM)

The **Coreason Agent Manifest (CAM)** is the primary "Source of Truth" for defining AI Agents and Workflows in the Coreason ecosystem. It uses a "Human-Centric" Canonical YAML format (`.yaml`) designed for ease of authoring, readability, and version control.

While developers write in this high-level format, the system compiles these manifests into machine-optimized "Runtime Definitions" ([Agent](runtime_agent_definition.md) or [Recipe](runtime_recipe_definition.md)) for execution by the engine.

## Root Object (`ManifestV2`)

The root of the document follows the "Kubernetes-style" header structure.

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
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

## 1. Interface (`InterfaceDefinition`)

Defines the contract for interacting with the component.

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

## 2. State (`StateDefinition`)

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

## 3. Policy (`PolicyDefinition`)

Defines execution limits and governance rules.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_steps` | `Optional[int]` | `None` | Execution limit on number of steps. |
| `max_retries` | `int` | `3` | Maximum number of retries for failed steps. |
| `timeout` | `Optional[int]` | `None` | Timeout in seconds. |
| `human_in_the_loop` | `bool` | `False` | Whether to require human approval. |

**Example:**
```yaml
policy:
  max_steps: 20
  timeout: 300
  human_in_the_loop: true
```

## 4. Workflow (`Workflow`)

Defines the steps and their flow. The V2 format uses an implicit "Linked List" approach via the `next` field in each step (simplifying the explicit edge lists used in runtime definitions).

| Field | Type | Description |
| :--- | :--- | :--- |
| `start` | `str` | The ID of the starting step. |
| `steps` | `Dict[str, Step]` | Dictionary of all steps indexed by ID. |

### Step Types

All steps include `id`, `inputs`, and `next` (except SwitchStep).

#### Agent Step (`type: agent`)
Executes an AI Agent.
- `agent`: Reference to an Agent definition (by ID or name).
- `system_prompt`: Optional override for system prompt.

#### Logic Step (`type: logic`)
Executes Python code.
- `code`: The Python code to execute or a reference to it.

#### Switch Step (`type: switch`)
Routes execution based on conditions.
- `cases`: Dictionary of condition expressions to Step IDs.
- `default`: Default Step ID if no cases match.
- *Note: Does not use `next`.*

#### Council Step (`type: council`)
Involves multiple voters/agents.
- `voters`: List of Agent IDs.
- `strategy`: Voting strategy (e.g., `consensus`, `majority`).

## Definitions (`definitions`)

The `definitions` section allows for reusable components, such as Tools. It supports the `$ref` syntax for importing definitions from other files.

**Example Tool Definition:**
```yaml
definitions:
  weather_tool:
    id: weather-tool
    name: Weather Tool
    uri: mcp://weather.com
    risk_level: safe
    description: Get weather info
```

## Example Manifest

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
workflow:
  start: "search"
  steps:
    search:
      type: agent
      id: "search"
      agent: "google_search"
      next: "summarize"

    summarize:
      type: agent
      id: "summarize"
      agent: "summarizer"
```
