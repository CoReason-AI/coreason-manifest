# Error Handling Standards

This document defines the standardized approach for handling and reporting errors within the Coreason ecosystem. By adhering to these standards, agents, engines, and frontends can provide a consistent, robust, and user-friendly experience.

## Overview

Coreason distinguishes between two types of errors:
1.  **Workflow Errors (`WorkflowError`)**: System-level or logic-level failures that occur during execution (e.g., "LLM API Timeout", "Database Connection Failed"). These are typically emitted as events.
2.  **User Errors (`UserErrorBlock`)**: UI-first artifacts designed to be shown to the end-user (e.g., "I couldn't find that file. Please upload it again.").

To support programmatic handling of these errors (e.g., auto-retries, specific UI icons), we enforce **Semantic Error Codes** and **Error Domains**.

## Semantic Error Codes

We utilize integer status codes inspired by standard HTTP response codes to convey the *nature* of the error.

| Range | Category | Description |
| :--- | :--- | :--- |
| **400-499** | Client/Input Errors | Issues caused by the user's input or request (e.g., Invalid Format, Missing Field). |
| **500-599** | System/Server Errors | Issues caused by the backend, LLM provider, or infrastructure (e.g., Timeout, Crash). |

### Common Codes

*   `400`: Bad Request / Validation Error
*   `401`: Unauthorized
*   `403`: Forbidden / Security Policy Violation
*   `404`: Not Found (Resource, Tool, or Knowledge)
*   `429`: Rate Limit Exceeded (Retryable)
*   `500`: Internal System Error (Generic)
*   `503`: Service Unavailable / Upstream API Failure (Retryable)
*   `504`: Timeout

## Error Domains

The `ErrorDomain` enum categorizes the *source* of the error. This helps frontends decide how to present the error (e.g., color-coding).

| Domain | Enum Value | Description |
| :--- | :--- | :--- |
| **System** | `SYSTEM` | Infrastructure, networking, or runtime engine failures. |
| **LLM** | `LLM` | Errors originating from the Large Language Model provider (e.g., refusal, context length exceeded). |
| **Tool** | `TOOL` | Errors occurring during the execution of an external tool or API. |
| **Logic** | `LOGIC` | Errors within the agent's reasoning or workflow graph (e.g., invalid state transition). |
| **Security** | `SECURITY` | Errors triggered by safety guardrails or policy enforcement. |

## WorkflowError Schema

The `WorkflowError` event payload (defined in `src/coreason_manifest/definitions/events.py`) includes these semantic fields:

```python
class WorkflowError(BaseNodePayload):
    # ... existing fields (error_message, stack_trace) ...

    # Semantic Fields
    code: int = 500
    domain: ErrorDomain = ErrorDomain.SYSTEM
    retryable: bool = False
```

*   **`code`**: The integer status code.
*   **`domain`**: The semantic source of the error.
*   **`retryable`**: A definitive flag indicating if the client (or engine) should attempt to retry the operation.

## UserErrorBlock Schema

The `UserErrorBlock` presentation artifact (defined in `src/coreason_manifest/definitions/presentation.py`) allows the UI to render semantic errors.

```python
class UserErrorBlock(PresentationBlock):
    # ... existing fields (user_message, etc.) ...

    code: Optional[int] = None
```

*   **`code`**: If provided, the UI can use this to select an appropriate icon (e.g., a "Disconnect" icon for `503`, a "Lock" icon for `403`).

## Usage Guidelines

### For Agent Developers
*   **Catch and Categorize:** When catching exceptions, try to map them to a specific `ErrorDomain` and `code`.
*   **Set Retryable:** Explicitly mark transient errors (like Rate Limits or Network Flakes) as `retryable=True`.

### For Frontend Developers
*   **Visual Cues:**
    *   `SYSTEM` / `SECURITY` errors might be red.
    *   `LLM` / `TOOL` errors might be amber/yellow.
*   **Auto-Retry:** If `retryable` is true (in a `WorkflowError`), consider showing a "Retry" button or automatically retrying the request after a backoff.
*   **Icons:** Map common codes (403, 404, 429, 500) to standard icon sets.
