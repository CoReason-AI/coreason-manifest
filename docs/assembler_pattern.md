# Assembler Pattern: Inline Agent Definition

The Coreason Manifest V2 supports the **Assembler Pattern**, allowing AI Agents to be defined directly within the Recipe Graph using the `construct` field. This eliminates the need for separate `AgentDefinition` files for simple or ad-hoc agents.

## Cognitive Profile

The `CognitiveProfile` model is the core component for inline agent definition. It specifies the agent's identity, reasoning architecture, and knowledge requirements.

### Schema

```python
class CognitiveProfile(CoReasonBaseModel):
    role: str = Field(..., description="The role or persona of the agent.")
    reasoning_mode: str = Field(..., description="The reasoning mode (e.g., 'react', 'cot').")

    # RAG Configuration
    memory: list[RetrievalConfig] = Field(
        default_factory=list, description="Configuration for Long-Term Memory (RAG) access."
    )

    # Dynamic Context Loading
    knowledge_contexts: list[str] = Field(default_factory=list, description="List of knowledge context IDs.")

    # Task Logic
    task_primitive: str | None = Field(None, description="The task primitive to execute.")
```

## Inline Definition in Recipe

You can define an agent inline within a `RecipeDefinition`'s topology:

```yaml
topology:
  nodes:
    - id: "writer"
      type: "agent"
      construct:
        role: "Content Writer"
        reasoning_mode: "cot"
        memory:
          - collection_name: "style_guide"
            strategy: "dense"
            top_k: 3
      system_prompt_override: "Write a blog post about AI."
```

## Benefits

*   **Self-Contained Recipes**: Define the entire workflow and agent logic in a single file.
*   **Rapid Prototyping**: Iterate on agent behavior without managing multiple files.
*   **Dynamic Assembly**: Supports programmatic construction of agents based on user intent.
