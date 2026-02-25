# Cognitive Profiles: Defining the Actor

In the `coreason-manifest` architecture, a **Cognitive Profile** defines the *identity* of an agent. It separates the "Who" (persona, expertise, role) from the "How" (reasoning engine, model selection).

The `CognitiveProfile` schema (`src/coreason_manifest/spec/core/nodes.py`) serves as the strict blueprint for an agent's behavioral bounds. It does not execute code; it configures the context in which reasoning occurs.

## The Schema

All profiles are strict Pydantic models inheriting from `CoreasonModel`.

```python
class CognitiveProfile(CoreasonModel):
    role: str
    persona: str
    reasoning: ReasoningConfig | None = None
    fast_path: FastPath | None = None
    domain_expertise: list[str] | None = None
```

### Core Attributes

*   **`role`**: The structural title of the agent (e.g., "Senior Financial Analyst", "Code Reviewer"). This is often used by Swarm routers or multi-agent orchestrators to select the correct worker for a task.
*   **`persona`**: The behavioral guardrails and tone. This field dictates the "System Prompt" content but is structurally separated to allow for static analysis of intent.
    *   *Example:* "You are objective, analytical, and heavily rely on cited sources. You never speculate."
*   **`domain_expertise`**: An optional list of specialized domains (e.g., `["finance", "python_coding"]`). This can be linked to global governance policies to restrict which agents are authorized to access sensitive tools or datasets.

## Reusability & Registry

Profiles are designed for maximum reusability across a graph.

### 1. Inline Definition
For one-off agents, the profile can be defined directly within the `AgentNode`.

```python
AgentNode(
    id="writer",
    profile=CognitiveProfile(
        role="Editor",
        persona="Fix grammar and tone."
    )
)
```

### 2. Global Registry (Reference by ID)
For consistent personas (e.g., a "Company-Wide Support Bot"), the profile is defined once in the Manifest's `definitions.profiles` registry and referenced by string ID. This ensures that if the persona is updated, every node using it inherits the change.

```python
# In definitions
profiles={
    "senior_dev": CognitiveProfile(role="Senior Dev", persona="...")
}

# In Graph
AgentNode(id="step_1", profile="senior_dev")
AgentNode(id="step_2", profile="senior_dev")
```
