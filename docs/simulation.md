# Agent Trajectory Interchange Format (ATIF)

## Introduction

The **Agent Trajectory Interchange Format (ATIF)** is a standardized schema for recording, persisting, and evaluating the execution history of autonomous agents. It transforms the system from a simple "execution engine" into a testable platform, enabling "Flight Recorder" capabilities for debugging, regression testing, and Red Teaming.

By adopting ATIF, we ensure that every action, thought, and observation of an agent can be captured in a structured, portable format. This format is essential for:

1.  **Debugging:** Replaying execution traces to identify logic flaws.
2.  **Regression Testing:** Verifying that changes to an agent do not degrade performance on known scenarios.
3.  **Red Teaming:** Systematically challenging agents with adversarial inputs and measuring their robustness.
4.  **Fine-tuning:** Using recorded trajectories to improve agent models.

## Core Models

All ATIF models inherit from `CoReasonBaseModel`, ensuring consistent serialization (JSON) and hashing behavior.

### 1. SimulationStep

The `SimulationStep` is the atomic unit of execution history. It captures a single event or action within an agent's lifecycle.

| Field | Type | Description |
| :--- | :--- | :--- |
| `step_id` | `UUID` | Unique identifier for the step (default: `uuid4`). |
| `timestamp` | `datetime` | UTC timestamp of the step (default: `datetime.now(UTC)`). |
| `type` | `StepType` | Category of the step (e.g., `interaction`, `tool_execution`). |
| `node_id` | `str` | ID of the graph node that executed this step. |
| `inputs` | `dict[str, Any]` | Inputs provided to the step (default: `{}`). |
| `thought` | `str \| None` | Internal monologue or Chain-of-Thought (CoT). |
| `action` | `dict[str, Any] \| None` | Tool call parameters or API request details. |
| `observation` | `dict[str, Any] \| None` | Tool output or API response. |
| `snapshot` | `dict[str, Any]` | Full state snapshot *after* execution (default: `{}`). |

**Step Types:**

*   `interaction`: User/Agent exchange.
*   `system_event`: Lifecycle event (e.g., startup, shutdown).
*   `tool_execution`: Calling an external tool.
*   `reasoning`: Chain of Thought block.
*   `error`: Exception captured during execution.

### 2. SimulationTrace

The `SimulationTrace` represents the full recording of a session, containing a sequence of `SimulationStep` objects.

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | `UUID` | Unique identifier for the trace (default: `uuid4`). |
| `agent_id` | `str` | Name or ID of the agent being tested. |
| `agent_version` | `str` | Semantic Version string of the agent. |
| `steps` | `list[SimulationStep]` | Chronological list of steps (default: `[]`). |
| `outcome` | `dict[str, Any] \| None` | Final result or output of the session. |
| `score` | `float \| None` | Evaluation score (0.0 to 1.0). |
| `metadata` | `dict[str, Any]` | Tags, environment info, git commit hash (default: `{}`). |

## Configuration Models

ATIF also defines schemas for configuring simulations and evaluations.

### 1. SimulationScenario

Defines a specific test case or scenario for an agent.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique ID for the scenario. |
| `description` | `str` | Human-readable description of the test. |
| `inputs` | `dict[str, Any]` | Initial inputs provided to the agent. |
| `expected_output` | `dict[str, Any] \| None` | Reference ground truth for validation. |
| `validation_logic` | `ValidationLogic` | Method used to grade the result. |

**Validation Logic:**

*   `exact_match`: Strict string equality.
*   `fuzzy`: Semantic similarity or flexible matching.
*   `code_eval`: Execution of code output.
*   `llm_judge`: Evaluation by another LLM.

### 2. AdversaryProfile

Configuration for a Red Team agent designed to challenge the target agent.

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Name of the adversary (e.g., "The Manipulator"). |
| `goal` | `str` | Objective of the adversary (e.g., "Extract PII"). |
| `strategy_model` | `str` | LLM used for planning (e.g., "claude-3-opus"). |
| `attack_model` | `str` | LLM used for execution (e.g., "llama-3-uncensored"). |
| `persona` | `dict[str, Any] \| None` | Serialized Persona definition. |

### 3. ChaosConfig

Configuration for injecting faults into the simulation environment.

| Field | Type | Description |
| :--- | :--- | :--- |
| `latency_ms` | `int` | Artificial latency in milliseconds (default: 0). |
| `error_rate` | `float` | Probability of error injection (default: 0.0). |
| `token_throttle` | `bool` | Whether to simulate token rate limiting (default: False). |

### 4. SimulationRequest

The trigger payload sent to the runner to initiate a simulation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `scenario` | `SimulationScenario` | The test case to run. |
| `profile` | `AdversaryProfile \| None` | Optional adversary configuration. |
| `chaos_config` | `ChaosConfig \| None` | Optional chaos configuration. |

## Usage Example

```python
from coreason_manifest import (
    SimulationTrace,
    SimulationStep,
    StepType,
    SimulationScenario,
    ValidationLogic
)
from datetime import UTC, datetime

# 1. Create a Scenario
scenario = SimulationScenario(
    id="test-001",
    description="Basic arithmetic check",
    inputs={"query": "What is 2 + 2?"},
    expected_output={"answer": "4"},
    validation_logic=ValidationLogic.EXACT_MATCH
)

# 2. Record Execution Steps
step1 = SimulationStep(
    type=StepType.INTERACTION,
    node_id="input_node",
    inputs=scenario.inputs,
    timestamp=datetime.now(UTC)
)

step2 = SimulationStep(
    type=StepType.REASONING,
    node_id="thinking_node",
    thought="The user is asking for a simple calculation. 2 + 2 = 4.",
    timestamp=datetime.now(UTC)
)

step3 = SimulationStep(
    type=StepType.INTERACTION,
    node_id="output_node",
    observation={"answer": "4"},
    timestamp=datetime.now(UTC)
)

# 3. Create a Trace
trace = SimulationTrace(
    agent_id="math-bot",
    agent_version="1.0.0",
    steps=[step1, step2, step3],
    outcome={"answer": "4"},
    score=1.0  # Perfect match
)

# 4. Serialize to JSON
print(trace.model_dump_json(indent=2))
```
