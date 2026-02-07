# Agent Trajectory Interchange Format (ATIF)

## Overview

The Agent Trajectory Interchange Format (ATIF) is a standardized schema for recording, analyzing, and exchanging agent execution history. It enables consistent evaluation, replay, and "Red Teaming" across different execution environments and evaluation platforms (e.g., Arize, LangSmith).

ATIF provides a "Flight Recorder" capability, capturing inputs, thoughts, actions, observations, and state snapshots for every step of an agent's lifecycle.

## Core Models

### `SimulationTrace`

The top-level container for a recorded session.

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | `UUID` | Unique identifier for the trace (default: `uuid4`). |
| `agent_id` | `str` | Name/ID of the agent being tested. |
| `agent_version` | `str` | Semantic version of the agent. |
| `steps` | `List[SimulationStep]` | Ordered list of execution steps. |
| `outcome` | `Dict[str, Any]` | Final result or output payload. |
| `score` | `float` | Evaluation score (0.0 to 1.0). Optional. |
| `metadata` | `Dict[str, Any]` | Tags, environment info, git commit hash. |

### `SimulationStep`

The atomic unit of execution history, representing a single node execution or event.

| Field | Type | Description |
| :--- | :--- | :--- |
| `step_id` | `UUID` | Unique identifier for the step. |
| `timestamp` | `datetime` | Execution timestamp (UTC). |
| `type` | `StepType` | Category of the step (e.g., `INTERACTION`, `TOOL_EXECUTION`). |
| `node_id` | `str` | ID of the graph node that executed. |
| `inputs` | `Dict[str, Any]` | Snapshot of data entering the node. |
| `thought` | `str` | Internal monologue or Chain of Thought (CoT). Optional. |
| `action` | `Dict[str, Any]` | Tool call parameters or API request. Optional. |
| `observation` | `Dict[str, Any]` | Tool output or API response. Optional. |
| `snapshot` | `Dict[str, Any]` | Full state snapshot *after* execution. |

#### `StepType` Enum

- `INTERACTION`: Exchange between user and agent.
- `SYSTEM_EVENT`: Lifecycle event (e.g., start, stop).
- `TOOL_EXECUTION`: Call to an external tool or API.
- `REASONING`: Internal deliberation or CoT block.
- `ERROR`: Exception or failure event.

## Configuration Models

### `SimulationRequest`

Defines the parameters for a simulation or evaluation run.

| Field | Type | Description |
| :--- | :--- | :--- |
| `scenario` | `SimulationScenario` | The test case to execute. |
| `profile` | `AdversaryProfile` | Configuration for Red Teaming (optional). |
| `chaos_config` | `ChaosConfig` | Configuration for fault injection (optional). |

### `AdversaryProfile`

Configures a Red Team agent to attack the target agent.

- `name`: Name of the adversary (e.g., "The Manipulator").
- `goal`: Objective (e.g., "Extract PII").
- `strategy_model`: LLM used for planning attacks.
- `attack_model`: LLM used for generating prompts.
- `persona`: Serialized persona definition.

### `ChaosConfig`

Configures infrastructure faults to test resilience.

- `latency_ms`: Artificial delay (ms).
- `error_rate`: Probability of failure (0.0 - 1.0).
- `token_throttle`: Simulate low throughput.

## Example JSON

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "research-assistant",
  "agent_version": "1.2.0",
  "steps": [
    {
      "step_id": "7b82f693-026f-4096-857e-324021204052",
      "timestamp": "2023-10-27T10:00:00Z",
      "type": "INTERACTION",
      "node_id": "input_node",
      "inputs": {
        "user_query": "What is the capital of France?"
      },
      "snapshot": {
        "state": "processing"
      }
    },
    {
      "step_id": "8c93a704-137a-5107-968f-435132315163",
      "timestamp": "2023-10-27T10:00:01Z",
      "type": "TOOL_EXECUTION",
      "node_id": "search_tool",
      "inputs": {
        "query": "capital of France"
      },
      "action": {
        "tool": "google_search",
        "args": {
          "q": "capital of France"
        }
      },
      "observation": {
        "result": "Paris"
      },
      "snapshot": {
        "state": "answering",
        "context": "Paris"
      }
    }
  ],
  "outcome": {
    "answer": "The capital of France is Paris."
  },
  "score": 1.0,
  "metadata": {
    "env": "staging",
    "model": "gpt-4"
  }
}
```
