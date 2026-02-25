# Evaluator-Optimizer Pattern

The **Evaluator-Optimizer** pattern is a core orchestration strategy in Coreason V2, designed to significantly improve the quality of AI-generated content through an iterative feedback loop. This pattern is inspired by the research in the [Anthropic Claude Cookbook](https://github.com/anthropics/claude-cookbook).

## Mental Model

Instead of relying on a single "zero-shot" generation from an LLM, this pattern introduces a two-step cycle:

1.  **Generate**: An Agent produces a draft.
2.  **Evaluate**: A separate "Judge" Agent critiques the draft against specific criteria and assigns a score.
3.  **Refine**: If the score is below a threshold, the critique is fed back to the Generator, which produces an improved draft.

This loop continues until the quality threshold is met or a maximum number of retries is reached.

## The `EvaluatorNode`

Coreason V2 simplifies this complex logic into a single declarative node type: `EvaluatorNode`.

### Schema Definition

```python
class EvaluatorNode(RecipeNode):
    type: Literal["evaluator"] = "evaluator"

    # What to grade
    target_variable: str

    # Who grades it
    evaluator_agent_ref: str
    evaluation_profile: EvaluationProfile | str

    # Logic
    pass_threshold: float
    max_refinements: int

    # Feedback Output
    feedback_variable: str

    # Flow Control
    pass_route: str
    fail_route: str
```

### Configuration Fields

*   **`target_variable`**: The key in the shared state (Blackboard) containing the content to be evaluated (e.g., `draft_body`).
*   **`evaluator_agent_ref`**: The ID of the Agent Definition that will act as the judge. This agent should be prompted to analyze content and produce structured critiques.
*   **`evaluation_profile`**: Defines the criteria for success. Can be an inline `EvaluationProfile` object or a reference ID string to a stored profile.
*   **`pass_threshold`**: A float between 0.0 and 1.0. If the evaluator's score is greater than or equal to this value, execution proceeds to `pass_route`.
*   **`max_refinements`**: The safety limit for the loop. If the threshold is not met after this many attempts, the flow will force a break (or a specific fallback if configured).
*   **`feedback_variable`**: The key where the critique text will be written. The Generator node *must* subscribe to this variable to incorporate the feedback.

## Example Usage

### YAML Recipe

```yaml
topology:
  nodes:
    # 1. The Generator (Writer)
    - type: agent
      id: "writer"
      agent_ref: "copywriter-v1"
      inputs_map:
        topic: "user_topic"
        # Crucial: This input allows the writer to see previous feedback
        critique: "critique_history"

    # 2. The Judge (Editor)
    - type: evaluator
      id: "editor-check"
      target_variable: "writer_output"
      evaluator_agent_ref: "editor-llm"

      # Criteria
      evaluation_profile: "marketing-compliance-v1"
      pass_threshold: 0.95
      max_refinements: 3

      # Feedback Loop
      feedback_variable: "critique_history"

      # Routing
      pass_route: "publish"
      fail_route: "writer" # Loop back

    # 3. Success
    - type: agent
      id: "publish"
      agent_ref: "publisher-v1"
```

## Best Practices

1.  **Strict Criteria**: The `evaluator_agent_ref` should use a system prompt that encourages critical, detailed feedback rather than generic praise.
2.  **History Awareness**: Ensure your Generator agent (e.g., "writer") is capable of understanding "critique" as an input argument.
3.  **Fallback Strategy**: While `EvaluatorNode` currently forces a loop, consider using a `RouterNode` after a maximum retry failure if you need a specific "give up" path (future feature).
