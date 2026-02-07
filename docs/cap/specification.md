# Coreason Agent Manifest (CAM)

The **Coreason Agent Manifest (CAM)** is the "Human-Centric" Canonical YAML format designed for defining Agents and Linear Workflows in the Coreason ecosystem. It serves as the primary interface for defining individual agents and simple, sequential recipes.

> **Note:** For complex, non-linear orchestration (loops, branching), see [Graph Recipes](../graph_recipes.md).

## Root Object (`ManifestV2`)

The root of the document follows a "Kubernetes-style" header structure.

```yaml
apiVersion: coreason.ai/v2
kind: Agent  # or 'Recipe' for linear workflows
metadata:
  name: "My Agent"
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
| `metadata` | `ManifestMetadata` | Metadata: `name`, `version`, `provenance`, and design info. |
| `interface` | `InterfaceDefinition` | Defines the Input/Output contract. |
| `state` | `StateDefinition` | Defines the internal memory schema. |
| `policy` | `PolicyDefinition` | Governance and execution policy. |
| `definitions` | `Dict[str, Any]` | Reusable component definitions (Tools, Agents, Skills, etc.). |
| `workflow` | `Workflow` | The main execution topology (Linear/Steps). |

## 1. Definitions Section

The `definitions` section is a polymorphic key-value map where you can define reusable components. These components can then be referenced by ID within the workflow.

Supported definitions include:
*   `AgentDefinition`
*   `ToolDefinition`
*   `SkillDefinition`
*   `MCPResourceDefinition`
*   `ToolPackDefinition`

### Tool Definition (`ToolDefinition`)
*   `type`: `tool`
*   `id`: Unique identifier.
*   `name`: Human-readable name.
*   `uri`: The MCP endpoint URI.
*   `risk_level`: `safe`, `standard`, or `critical`.
*   `description`: Description of the tool.

### Agent Definition (`AgentDefinition`)
*   `type`: `agent`
*   `id`: Unique identifier.
*   `name`: Agent name.
*   `role`: The persona/job title.
*   `goal`: The primary objective.
*   `backstory`: Detailed instructions or persona background.
*   `model`: LLM identifier (e.g., `gpt-4`).
*   `tools`: List of tools. Supports:
    *   **ID Reference**: String pointing to a `ToolDefinition`.
    *   **Remote Tool (`ToolRequirement`)**: Object with `type: remote`, `uri`, and optional `hash`.
    *   **Inline Tool (`InlineToolDefinition`)**: Object with `type: inline`, `name`, `description`, `parameters` (JSON Schema), and optional `code_hash`.
*   `skills`: List of Skill IDs to equip this agent with.
*   `knowledge`: List of file paths or knowledge base IDs.
*   `context_strategy`: `full`, `compressed`, or `hybrid` (Default: `hybrid`).
*   `capabilities`: Feature flags and capabilities.
*   `runtime`: Configuration for the agent runtime environment (e.g. environment variables).
*   `evaluation`: Quality assurance and testing metadata (`EvaluationProfile`).
*   `resources`: Hardware, pricing, and operational constraints (`ModelProfile`).

### Agent Capabilities (`AgentCapabilities`)
Used within an `AgentDefinition` to declare supported features. See [Explicit Streaming Contracts](streaming_contracts.md) for detailed definitions.

*   `type`: The architectural complexity of the agent (`atomic`, `graph`).
*   `delivery_mode`: Primary transport mechanism (`server_sent_events`, `request_response`).
*   `history_support`: Boolean indicating if the agent maintains conversation context.

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
    description: "Search the web for information."

  # Define a Native Agent
  writer_agent:
    type: agent
    id: writer
    name: Content Writer
    role: Senior Editor
    goal: Summarize research into a blog post.
    backstory: You are an expert editor with a focus on clarity.
    tools: ["search"] # References the tool ID above
    skills: ["writing-skill"]
    model: "gpt-4"
    context_strategy: "compressed"
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

## 4. Policy (`PolicyDefinition`)

Defines execution limits and governance rules.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_steps` | `Optional[int]` | `None` | Execution limit on number of steps. |
| `max_retries` | `int` | `3` | Maximum number of retries for failed steps. |
| `timeout` | `Optional[int]` | `None` | Timeout in seconds. |
| `human_in_the_loop` | `bool` | `False` | Whether to require human approval. |

## 5. Workflow (`Workflow`)

Defines the linear execution topology. For graph-based topology (loops, branches), use `RecipeDefinition`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `start` | `str` | The ID of the starting step. |
| `steps` | `Dict[str, Step]` | Dictionary of all steps indexed by ID. |

### Step Types

All steps include `id`, `inputs`, and `design_metadata` (alias `x-design`).

#### Agent Step (`type: agent`)
Executes an AI Agent.
- `agent`: Reference to an Agent definition (by ID or name).
- `next`: ID of the next step to execute.
- `system_prompt`: Optional override for system prompt.
- `temporary_skills`: List of skills injected into the agent ONLY for this specific step.

#### Logic Step (`type: logic`)
Executes Python code.
- `code`: The Python code or reference to logic to execute.
- `next`: ID of the next step to execute.

#### Switch Step (`type: switch`)
Routes execution based on conditions.
- `cases`: Dictionary of condition expressions to Step IDs.
- `default`: Default Step ID if no cases match.
- *Note: Does not use `next`.*

#### Council Step (`type: council`)
Involves multiple voters/agents.
- `voters`: List of Agent IDs.
- `strategy`: Voting strategy (e.g., `consensus`, `majority`).
- `next`: ID of the next step to execute.

## Complete Example Manifest (Linear Recipe)

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Research Workflow"
  version: "1.0.0"
  provenance:
    type: "human"
    generated_by: "Alice"
    methodology: "Manual Design"
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
    description: "Search engine."

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
