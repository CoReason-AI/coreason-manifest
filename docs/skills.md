# Agent Skills System

## Overview

The **Agent Skills System** in `coreason-manifest` introduces a standardized way to define, package, and distribute "Procedural Knowledge" for AI Agents. This system aligns with State-of-the-Art (SOTA) patterns found in frameworks like Anthropic's Agent Skills and Microsoft's Semantic Kernel.

Unlike **Tools** (which are active functions) or **Knowledge** (which is passive data), **Skills** represent *how-to* knowledge—playbooks, standard operating procedures (SOPs), and specialized workflows that an agent can "learn" and execute.

## Core Concepts

### 1. Skill Definition
A `SkillDefinition` is a portable unit of expertise. It encapsulates:
- **Discovery Metadata**: How the router finds the skill (`trigger_intent`).
- **Instructional Context**: The system prompt or guide (`instructions` / `SKILL.md`).
- **Execution Capabilities**: Scripts and dependencies required to perform the skill.
- **Lifecycle Management**: Strategies for loading the skill into the context window.

### 2. Load Strategies
To optimize context window usage, skills support different loading strategies:

- **`EAGER`**: The skill's instructions are always loaded into the agent's system prompt at startup. Best for core competencies.
- **`LAZY`**: The skill is only loaded when the user's intent matches the `trigger_intent`. Best for specialized or rarely used skills.
- **`USER`**: The skill is exposed as a client-side command (e.g., slash command) and triggered explicitly by the user.

### 3. Dependencies
Skills can declare dependencies on external packages or system tools, ensuring the runtime environment is correctly provisioned.

## Schema Reference

### `SkillDefinition`

| Field | Type | Description |
| :--- | :--- | :--- |
| `type` | `Literal["skill"]` | Discriminator field. |
| `id` | `str` | Unique identifier for the skill. |
| `name` | `str` | Human-readable name. |
| `description` | `str` | Summary for humans. |
| `trigger_intent` | `str` | **Critical.** Semantic description for vector routing. Required if `load_strategy` is `LAZY`. |
| `instructions` | `str` | Inline system prompt. (XOR with `instructions_uri`) |
| `instructions_uri` | `str` | Path to external `SKILL.md` file. (XOR with `instructions`) |
| `scripts` | `dict[str, str]` | Map of script names to file paths. |
| `dependencies` | `list[SkillDependency]` | List of required packages. |
| `load_strategy` | `LoadStrategy` | `eager`, `lazy`, or `user`. Defaults to `lazy`. |

### `AgentDefinition` Update

Agents now possess a `skills` field and a `context_strategy`:

```python
class AgentDefinition(CoReasonBaseModel):
    # ...
    skills: list[str] = Field(..., description="List of Skill IDs to equip this agent with.")
    context_strategy: Literal["full", "compressed", "hybrid"] = Field(
        "hybrid", description="Context optimization strategy for skills."
    )
```

### `AgentStep` Update

Skills can be injected temporarily for a specific step in the workflow:

```python
class AgentStep(BaseStep):
    # ...
    temporary_skills: list[str] = Field(..., description="Skills injected into the agent ONLY for this specific step.")
```

## Example Usage

### 1. Defining a Skill (YAML)

```yaml
definitions:
  pdf-processing:
    type: skill
    id: pdf-processing
    name: "PDF Master"
    version: "1.0.0"
    load_strategy: lazy
    # Trigger intent is mandatory for LAZY loading
    trigger_intent: "User wants to merge, split, or extract text from PDF files."

    # Point to an external markdown file for detailed instructions
    instructions_uri: "./skills/pdf/SKILL.md"

    # Scripts required by this skill
    scripts:
      merge: "./skills/pdf/scripts/merge.py"
      extract: "./skills/pdf/scripts/extract.py"

    # Runtime dependencies
    dependencies:
      - ecosystem: python
        package: pypdf
        version_constraint: ">=3.0.0"
```

### 2. Equipping an Agent

```yaml
definitions:
  clerk-agent:
    type: agent
    id: clerk-agent
    role: "Clerk"
    goal: "Process paperwork efficiently."

    # Reference the skill by ID
    skills:
      - "pdf-processing"
```

## Best Practices

1. **Semantic Trigger Intents**: Write `trigger_intent` as a distinct, semantic description of *when* to use the skill, optimized for embedding models.
2. **Lazy by Default**: Prefer `lazy` loading to keep the agent's context window clean and focused. Use `eager` only for skills the agent uses in almost every turn.
3. **Externalize Instructions**: For complex skills, use `instructions_uri` to keep the manifest clean and leverage standard Markdown editing for the skill documentation.
