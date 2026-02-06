# Evaluation-Ready Metadata

Coreason Agents are designed to be "self-describing" not just in their capability and structure, but also in how their quality and performance should be measured. The **Evaluation Metadata** specification embeds testing requirements, golden datasets, and grading rubrics directly into the `AgentDefinition`.

This ensures that the "Definition of Done" for an agent travels with the agent itself, preventing drift between the implementation and its quality checks.

## Data Model

### Evaluation Profile

The `EvaluationProfile` is an optional component of an `AgentDefinition`. It defines the environment, datasets, and criteria used to certify the agent.

```python
class EvaluationProfile(CoReasonBaseModel):
    expected_latency_ms: int | None
    golden_dataset_uri: str | None
    evaluator_model: str | None
    grading_rubric: list[SuccessCriterion]
```

*   **`expected_latency_ms`**: Service Level Agreement (SLA) for the maximum acceptable response time in milliseconds.
*   **`golden_dataset_uri`**: A URI (e.g., `s3://`, `http://`) pointing to the standardized test dataset (Golden Set) used for evaluation.
*   **`evaluator_model`**: The ID of the LLM model to be used as a "Judge" for semantic evaluation (e.g., `gpt-4`, `claude-3-opus`).
*   **`grading_rubric`**: A list of specific criteria that the agent must meet.

### Success Criterion

A `SuccessCriterion` defines a single metric or qualitative check.

```python
class SuccessCriterion(CoReasonBaseModel):
    name: str
    description: str
    threshold: float
    strict: bool = True
```

*   **`name`**: A machine-readable identifier for the metric (e.g., `answer_relevance`, `hallucination_rate`).
*   **`description`**: A human-readable explanation of what is being measured.
*   **`threshold`**: The numerical score required to pass (e.g., `0.9` for 90%).
*   **`strict`**: If `True` (default), failure of this criterion blocks deployment or certification. If `False`, it is treated as a warning.

## Example Usage

### YAML Definition

When defining an agent in a Manifest (YAML):

```yaml
definitions:
  research-agent:
    type: agent
    id: research-agent
    name: "Senior Researcher"
    role: "Research Analyst"
    goal: "Provide accurate summaries of financial data."
    model: "gpt-4"
    evaluation:
      expected_latency_ms: 2000
      golden_dataset_uri: "s3://coreason-datasets/finance-qa-v1.json"
      evaluator_model: "gpt-4-turbo"
      grading_rubric:
        - name: "factuality"
          description: "Ensure no hallucinations in financial figures."
          threshold: 0.99
          strict: true
        - name: "conciseness"
          description: "Summary length ratio."
          threshold: 0.80
          strict: false
```

### Programmatic Access

```python
from coreason_manifest import Manifest, AgentDefinition

# Load the manifest
manifest = Manifest.load("agent.yaml")
agent = manifest.definitions["research-agent"]

# Access evaluation metadata
if agent.evaluation:
    print(f"Testing against: {agent.evaluation.golden_dataset_uri}")

    for criterion in agent.evaluation.grading_rubric:
        print(f" - {criterion.name}: Target {criterion.threshold}")
```
