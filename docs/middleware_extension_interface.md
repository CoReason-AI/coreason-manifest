# Middleware Extension Interface

The Middleware Extension Interface allows developers to inject custom logic *before* and *after* agent execution. This enables cross-cutting concerns such as PII redaction, toxicity filtering, rate limiting, and observability to be implemented cleanly and reusable across different agents.

## Core Concepts

The middleware system is built on two primary protocols: `IRequestInterceptor` for input processing and `IResponseInterceptor` for output stream modification. Both protocols share a common `InterceptorContext`.

### InterceptorContext

A lightweight, immutable object used to pass shared data and metadata between interceptors in a chain.

```python
class InterceptorContext(CoReasonBaseModel):
    """A lightweight immutable object to pass shared data between interceptors."""

    request_id: UUID
    start_time: datetime
    metadata: Dict[str, Any]
```

## Protocols

### IRequestInterceptor

Implement this protocol to intercept, modify, or validate an incoming `AgentRequest` before it reaches the agent.

```python
@runtime_checkable
class IRequestInterceptor(Protocol):
    """Protocol for intercepting and modifying agent requests."""

    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        """Modify or validate the request before the agent sees it."""
        ...
```

**Common Use Cases:**
- **PII Redaction:** scrubbing sensitive data from the prompt.
- **Input Validation:** Ensuring the request meets schema requirements.
- **Security Checks:** Verifying permissions or quotas.

### IResponseInterceptor

Implement this protocol to intercept and modify the outgoing `StreamPacket` stream in real-time.

```python
@runtime_checkable
class IResponseInterceptor(Protocol):
    """Protocol for intercepting and modifying the output stream."""

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        """Modify the output stream in real-time."""
        ...
```

**Common Use Cases:**
- **Toxicity Filtering:** checking generated tokens for harmful content.
- **Format Standardization:** Enforcing specific output structures.
- **Audit Logging:** creating a shadow copy of the stream for compliance.

## Usage Example

```python
from coreason_manifest.definitions.middleware import IRequestInterceptor, IResponseInterceptor

class PIIFilter(IRequestInterceptor):
    async def intercept_request(self, context, request):
        # ... logic to redact PII ...
        return redacted_request

class ContentSafetyFilter(IResponseInterceptor):
    async def intercept_stream(self, packet):
        # ... logic to check packet content ...
        return packet
```
