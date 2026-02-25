# Explicit Streaming Contracts

The Coreason Agent Manifest (CAM) V2 enforces explicit contracts between Agents and Clients regarding execution behavior and transport protocols. This removes ambiguity and allows clients to deterministicly handle agent interactions.

## Core Concepts

The contract is defined in `AgentCapabilities` and consists of two primary dimensions:

1.  **Architectural Complexity (`type`)**
2.  **Delivery Mode (`delivery_mode`)**

### 1. Architectural Complexity (`type`)

Defines the internal structure and execution model of the agent.

*   **`atomic`**:
    *   **Description:** A simple, linear agent that executes a single logical step (e.g., an LLM call, a tool execution).
    *   **Behavior:** Typically fast, synchronous or single-stream.
    *   **Use Case:** Chatbots, simple lookups, "functions as agents".

*   **`graph`**:
    *   **Description:** A complex agent composed of multiple steps, loops, or a directed acyclic graph (DAG).
    *   **Behavior:** Long-running, multi-step execution. Often requires intermediate state updates.
    *   **Use Case:** Research assistants, coding agents, multi-agent workflows.
    *   **Default:** This is the default type if not specified.

### 2. Delivery Mode (`delivery_mode`)

Defines the transport protocol used to deliver results.

*   **`request_response`**:
    *   **Description:** Standard Synchronous HTTP (REST).
    *   **Behavior:** The client sends a request and waits for a single, final JSON response.
    *   **Constraint:** Best for `atomic` agents or very short `graph` executions.
    *   **Default:** This is the default mode if not specified.

*   **`server_sent_events`**:
    *   **Description:** Streaming CloudEvents via Server-Sent Events (SSE).
    *   **Behavior:** The client connects and receives a stream of events (`CloudEvent`) representing progress, partial thoughts, reasoning traces, and the final result.
    *   **Constraint:** Recommended for `graph` agents or `atomic` agents generating long text (LLM streaming).
    *   **Note:** Replaces the legacy `sse` abbreviation.

## Valid Configurations

| Type | Delivery Mode | Scenario |
| :--- | :--- | :--- |
| `atomic` | `request_response` | **Simple API**: A calculator tool or quick lookup. |
| `atomic` | `server_sent_events` | **Streaming Chat**: A simple LLM wrapper streaming tokens. |
| `graph` | `request_response` | **Batch Job**: A background process where intermediate progress isn't watched (uncommon for interactive apps). |
| `graph` | `server_sent_events` | **Interactive Workflow**: A complex agent (e.g., Researcher) streaming its thought process and steps to the user. |

## Schema Example

```yaml
definitions:
  my_researcher:
    type: agent
    id: researcher
    capabilities:
      type: graph
      delivery_mode: server_sent_events
      history_support: true
```
