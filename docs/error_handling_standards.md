# Semantic Error Handling Standards

This document defines the standard for Semantic Error Handling in the CoReason ecosystem. The goal is to move from generic exceptions to structured, machine-readable error codes and user-friendly error events.

## Concepts

### Error Domains

Errors are categorized into "Domains" to help consumers (UIs, Agents) understand the source of the failure.

| Domain | Value | Description |
| :--- | :--- | :--- |
| **CLIENT** | `client` | The request was invalid (e.g., 4xx HTTP range). |
| **SYSTEM** | `system` | Internal platform failure (e.g., database down, 5xx HTTP range). |
| **LLM** | `llm` | Failure from the Model Provider (e.g., overloaded, refusal). |
| **TOOL** | `tool` | Failure execution of an external tool (MCP, API). |
| **SECURITY** | `security` | Authentication, Authorization, or Governance rejection. |

These are defined in the `ErrorDomain` enum in `coreason_manifest`.

### User Error Event

The `UserError` is a specialized `PresentationEvent` type (`type="user_error"`) designed to be rendered directly to the end-user. It allows the backend to control the error messaging, iconography (via domain), and retry logic.

It is part of the `PresentationEvent` structure and can be streamed via `StreamPacket` (op=`event`).

**Schema:**

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `type` | `Literal["user_error"]` | - | Discriminator. |
| `data` | `Dict` | - | Payload containing error details. |

**Data Payload:**

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `message` | `str` | - | Human-readable message. |
| `code` | `Optional[int]` | `None` | Semantic integer code (e.g., 400, 429, 503). |
| `domain` | `ErrorDomain` | `system` | Source of the error. |
| `retryable` | `bool` | `False` | Whether the client should suggest a retry. |

**Example JSON:**

```json
{
  "id": "...",
  "timestamp": "...",
  "type": "user_error",
  "data": {
    "message": "The search tool is currently unavailable. Please try again later.",
    "code": 503,
    "domain": "tool",
    "retryable": true
  }
}
```

## Usage

### When to use `UserError` vs `StreamError`?

*   **`StreamError` (CAP)**: Use this for protocol-level failures where the stream itself is broken or the agent has crashed fatally. This is a "System Exception".
*   **`UserError` (Presentation)**: Use this when the agent is still healthy, but a specific sub-task failed (e.g., a tool failed), and you want to inform the user gracefully without crashing the conversation. This is a "User Notification".
