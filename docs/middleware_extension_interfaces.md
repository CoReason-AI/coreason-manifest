# Middleware Extension Interfaces

The Coreason Engine provides a standardized way to inject cross-cutting logic—such as PII redaction, Rate Limiting, and Toxicity Filtering—into the agent runtime without modifying core code. This is achieved through strict **Interoperability Protocols** defined in the Shared Kernel.

## Overview

The middleware system relies on strict Python protocols (`typing.Protocol`) and immutable data models. Extension developers implement these protocols to intercept requests (input) or streams (output).

### Key Components

| Component | Type | Description |
| :--- | :--- | :--- |
| `InterceptorContext` | Model | Immutable context containing metadata about the interception point. |
| `IRequestInterceptor` | Protocol | Contract for modifying or validating `AgentRequest` objects before execution. |
| `IResponseInterceptor` | Protocol | Contract for inspecting or modifying `StreamPacket` objects during output streaming. |

## Data Models

### InterceptorContext

The `InterceptorContext` provides metadata about the current transaction. It is an immutable Pydantic model.

```python
from coreason_manifest import InterceptorContext
from datetime import UTC, datetime
from uuid import uuid4

ctx = InterceptorContext(
    request_id=uuid4(),
    start_time=datetime.now(UTC),
    metadata={"source": "api_gateway"}
)
```

**Fields:**

*   `request_id` (`UUID`): Unique identifier for the request being intercepted.
*   `start_time` (`datetime`): Timestamp when the interception context was initialized.
*   `metadata` (`dict[str, Any]`): Arbitrary metadata (e.g., headers, tracing info). Defaults to `{}`.

## Protocols

### IRequestInterceptor

Implement this protocol to intercept incoming requests. Common use cases include PII redaction, prompt injection detection, and request validation.

```python
from typing import Protocol, runtime_checkable
from coreason_manifest import AgentRequest, InterceptorContext

@runtime_checkable
class IRequestInterceptor(Protocol):
    async def intercept_request(
        self,
        context: InterceptorContext,
        request: AgentRequest
    ) -> AgentRequest:
        """Modify or validate the request before the agent sees it."""
        ...
```

**Example Implementation (PII Redactor):**

```python
class PIIRedactor:
    async def intercept_request(
        self,
        context: InterceptorContext,
        request: AgentRequest
    ) -> AgentRequest:
        # Simple example: Redact generic credit card numbers in query
        if "4000-1234" in request.query:
            # Create a modified copy (AgentRequest is immutable)
            return request.model_copy(
                update={"query": request.query.replace("4000-1234", "XXXX-XXXX")}
            )
        return request
```

### IResponseInterceptor

Implement this protocol to intercept the outgoing stream. Common use cases include toxicity filtering, audit logging, and format transformation.

```python
from typing import Protocol, runtime_checkable
from coreason_manifest import StreamPacket

@runtime_checkable
class IResponseInterceptor(Protocol):
    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        """Modify the output stream in real-time."""
        ...
```

**Example Implementation (Toxicity Filter):**

```python
from coreason_manifest import StreamOpCode, StreamError, ErrorSeverity

class ToxicityFilter:
    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        # Check text deltas for toxic content
        if packet.op == StreamOpCode.DELTA and isinstance(packet.p, str):
            if "bad_word" in packet.p:
                # Replace the packet with an error or redacted content
                return StreamPacket(
                    op=StreamOpCode.ERROR,
                    p=StreamError(
                        code="TOXICITY_DETECTED",
                        message="Content was blocked due to safety policy.",
                        severity=ErrorSeverity.TRANSIENT
                    )
                )
        return packet
```
