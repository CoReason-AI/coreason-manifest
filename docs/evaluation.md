# Evaluation-Ready Metadata

The **Evaluation-Ready Metadata** feature allows agents to carry their own test contracts, ensuring that every agent asset defines its own success criteria, golden datasets, and SLAs.

## Overview

Traditionally, evaluation logic is decoupled from the agent definition, leading to drift between the agent's behavior and its tests. By embedding evaluation metadata directly into the `AgentDefinition`, we ensure that the agent is self-describing regarding its quality and performance expectations.

## The Evaluation Profile

The `EvaluationProfile` class (located in `src/coreason_manifest/definitions/evaluation.py`) is the container for this metadata. It is an optional field (`evaluation`) in the `AgentDefinition`.

### Components

1.  **SLA (`expected_latency_ms`)**:
    *   Defines the expected maximum response time in milliseconds.
    *   Useful for performance testing and monitoring.

2.  **Golden Dataset (`golden_dataset_uri`)**:
    *   A URI pointing to a reference dataset used for evaluation.
    *   This ensures that the test data is versioned alongside the agent.

3.  **Grading Rubric (`grading_rubric`)**:
    *   A list of `SuccessCriterion` objects defining specific quality checks.
    *   Each criterion has a `name`, `description`, `threshold`, and `strict` flag.

4.  **Evaluator Model (`evaluator_model`)**:
    *   Specifies the model to be used for LLM-as-a-Judge evaluations (e.g., "gpt-4-turbo").

## Success Criterion

The `SuccessCriterion` model defines a single condition for success.

*   `name`: The unique name of the criterion (e.g., "json_schema_validity", "semantic_similarity").
*   `description`: A human-readable description of what is being checked.
*   `threshold`: A numerical threshold for the check (e.g., 0.95).
*   `strict`: A boolean indicating if this is a hard requirement (default: `True`).

## Example Usage

```python
from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.evaluation import EvaluationProfile, SuccessCriterion

agent = AgentDefinition(
    # ... other fields ...
    evaluation=EvaluationProfile(
        expected_latency_ms=2000,
        golden_dataset_uri="s3://datasets/weather-gold-v1.json",
        evaluator_model="gpt-4-turbo",
        grading_rubric=[
            SuccessCriterion(
                name="response_conciseness",
                description="Ensure the response is under 50 words.",
                strict=False
            ),
            SuccessCriterion(
                name="json_validity",
                description="Ensure the output is valid JSON.",
                strict=True
            )
        ]
    )
)
```
