# RFC 004: CAP Client SDK Reference Architecture

**File Path:** `docs/rfcs/004-cap-client-sdk.md`
**Status:** Draft

## 1. Context and Scope

This document defines the technical specification for the official **Coreason Agent Protocol (CAP) Client SDK** for Python.

The CAP Client serves as the bridge between the strict, formal wire protocols defined in our system and the everyday developer experience. It must strictly adhere to the following authoritative specifications while providing a "magical" and robust user experience:

*   **Wire Protocol:** `docs/sse_wire_protocol.md` (Defines `StreamPacket`, `StreamOpCode`, and the `DELTA`/`EVENT` payload structures).
*   **Service Interface:** `docs/interface_contracts.md` (Defines the `/assist` endpoint and the `ServiceRequest` envelope).
*   **Message Definitions:** `src/coreason_manifest/definitions/message.py` (Defines `ChatMessage` and `Role`).

The scope of this RFC is limited to the **client-side implementation** of these protocols. It does not propose changes to the wire format or the server-side contracts.

## 2. Design Goals

### 2.1. Strict Protocol Compliance (The "Law")
The client must be a faithful implementation of the Coreason Agent Protocol. It must **not** invent new concepts that do not exist on the wire.
*   It must produce valid `ServiceRequest` envelopes.
*   It must consume and validate `StreamPacket` objects exactly as defined in the SSE Wire Protocol.
*   It must reject invalid payloads immediately (fail fast) using Pydantic validation.

> **Note:** This RFC mandates the use of **POST** for the `/assist` endpoint due to the complexity of the `ServiceRequest` body. This explicitly supersedes older versions of `sse_wire_protocol.md` that may reference `GET`.

### 2.2. Developer Magic (The "Experience")
While the protocol is strict, the developer experience (DX) should be fluid.
*   **Transparency:** Network interruptions should be invisible. The client must handle SSE reconnection, cursor management (`Last-Event-ID`), and deduplication automatically.
*   **Abstraction:** For 90% of use cases (chat), the developer should not need to construct complex JSON envelopes. A simple string-in, string-out interface is required.

## 3. Architecture Specification

### 3.1. The `CAPClient` Class Structure

The `CAPClient` is the primary entry point. It wraps an HTTP client (e.g., `httpx.Client`) and manages the session state for connection resilience.

```python
from typing import Generator, Optional, List, Dict, Any, Union
from uuid import UUID, uuid4
import httpx
from coreason_manifest.definitions.presentation import StreamPacket, StreamOpCode
from coreason_manifest.definitions.service import ServiceRequest
from coreason_manifest.definitions.message import ChatMessage

class ChatStream:
    """
    A wrapper around the stream generator that exposes metadata.
    Allows the developer to retrieve the conversation_id even while iterating.
    """
    def __init__(self, generator: Generator[str, None, None], conversation_id: str):
        self._gen = generator
        self.conversation_id = conversation_id

    def __iter__(self) -> Generator[str, None, None]:
        return self._gen

class CAPClient:
    def __init__(self, base_url: str, api_key: str, timeout: Union[float, httpx.Timeout] = 60.0, max_retries: int = 3):
        """
        Initializes the CAP Client.

        Args:
            base_url: The root URL of the Coreason Agent service.
            api_key: Authentication credential.
            timeout: Read timeout in seconds (default 60.0).
            max_retries: Maximum number of reconnection attempts (default 3).
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        # Configure internal HTTP client with appropriate timeouts
        self._http = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout if isinstance(timeout, httpx.Timeout) else httpx.Timeout(connect=10.0, read=timeout)
        )

    def assist(self, request: ServiceRequest) -> Generator[StreamPacket, None, None]:
        """
        The Strict Interface (Method 1).

        Fully typed, low-level access to the agent.

        Args:
            request: A fully constructed and validated ServiceRequest envelope.

        Yields:
            Strictly validated StreamPacket objects.

        Raises:
            CAPConnectionError: If retries are exhausted.
            CAPProtocolError: If the server sends invalid data.
            CAPRuntimeError: If the stream contains an error packet.
        """
        # Implementation of the Transparency Logic (see 3.2)
        yield from self._event_loop(request)

    def chat(self, message: str, conversation_id: Optional[str] = None) -> "ChatStream":
        """
        The DX Convenience Interface (Method 2).

        Abstracts away the ServiceRequest envelope and StreamPacket parsing.
        Returns a ChatStream object which iterates over text deltas
        and exposes the .conversation_id property.

        Args:
            message: The user's query string.
            conversation_id: Optional ID to continue a session.

        Returns:
            ChatStream: An iterable object containing the stream and metadata.
        """
        # 1. Construct the Context
        if conversation_id is None:
            conversation_id = str(uuid4()) # Generate ID client-side if missing

        # (Internal logic to build SessionContext and AgentRequest)

        # 2. Call the strict interface
        # request = ... (construction logic using conversation_id)
        packet_generator = self.assist(request)

        # 3. Create the generator logic
        def _stream_gen():
            for packet in packet_generator:
                if packet.op == StreamOpCode.DELTA:
                    # Type narrowing ensures this is a string
                    yield str(packet.p)
                elif packet.op == StreamOpCode.ERROR:
                    raise CAPRuntimeError(f"Stream Error: {packet.p}")
                # Silently ignore EVENT, CLOSE, etc. for simple chat mode

        return ChatStream(_stream_gen(), conversation_id)
```

### 3.2. The "Transparency" Logic

The core value proposition of this SDK is the robust handling of the SSE event loop. The client implements a **self-healing iterator** that masks network instability.

#### Algorithm: `_event_loop`

The `_event_loop` method implements the following state machine:

1.  **Initialization:**
    *   Set `last_id = None`.
    *   Set `last_seq = -1`.
    *   Initialize `backoff_delay = 0.5` seconds.

2.  **Connection Loop:**
    *   `while True:` (Until explicit CLOSE or max retries)
    *   **Attempt Connection:**
        *   Send `POST /assist`.
        *   Headers:
            1. Include `Last-Event-ID: {last_id}` if `last_id` is not None.
            2. Ensure `X-Request-ID` or the body `request_id` matches the **original** attempt to prevent duplicate processing.
        *   Body: The original `ServiceRequest` JSON.

    *   **Process Stream:**
        *   If response is 200 OK:
            *   Reset `backoff_delay` to initial value.
            *   Iterate over SSE lines (`data: ...`).
            *   Parse line into `StreamPacket`.
            *   **Deduplication Check:**
                *   If `packet.seq <= last_seq`: **DISCARD** (Duplicate replay).
                *   Else:
                    *   Update `last_seq = packet.seq`.
                    *   Update `last_id = packet.stream_id`.
                    *   Yield `packet`.
            *   **Termination Check:**
                *   If `packet.op == StreamOpCode.CLOSE`: `break` (Exit loop).

    *   **Error Handling (Resume):**
        *   If `httpx.StreamError`, `httpx.NetworkError`, or `ChunkedEncodingError`:
            *   Log warning: "Connection dropped. Retrying in X seconds..."
            *   `sleep(backoff_delay)` (Use `asyncio.sleep` for AsyncClient).
            *   `backoff_delay = min(backoff_delay * 2, 30.0)` (Exponential Backoff).
            *   `continue` (Retry loop with `Last-Event-ID`).

        *   If `httpx.HTTPStatusError` (4xx/5xx):
            *   Raise `CAPRuntimeError` (Do not retry client errors).

### 3.3. Async Support

To support modern, high-concurrency applications, the SDK must provide an asynchronous counterpart to `CAPClient`.

*   **Class Name:** `AsyncCAPClient`
*   **Dependencies:** `httpx.AsyncClient`
*   **Interface:** Mirrors `CAPClient` 1:1, but all methods are `async` and return `AsyncGenerator`.

```python
class AsyncCAPClient:
    async def assist(self, request: ServiceRequest) -> AsyncGenerator[StreamPacket, None]:
        ...

    async def chat(self, message: str, conversation_id: Optional[str] = None) -> "AsyncChatStream":
        ...
```

The `AsyncChatStream` wrapper similarly implements `__aiter__` instead of `__iter__`.

## 4. Usage Examples

### Scenario A: Easy Mode (Simple Chat)

Perfect for quick scripts, CLI tools, or simple chatbots.

```python
from coreason_client import CAPClient

client = CAPClient(base_url="https://api.coreason.ai", api_key="sk_...")

print("User: Explain quantum mechanics.")
print("AI: ", end="", flush=True)

# The stream object holds the ID for the next turn
stream = client.chat("Explain quantum mechanics.")

for chunk in stream:
    print(chunk, end="", flush=True)

# Continue conversation
next_stream = client.chat("How does that relate to gravity?", conversation_id=stream.conversation_id)
# ...
```

### Scenario B: Power User (Complex Request)

Required for multi-modal inputs, explicit context management, or accessing rich UI events.

```python
from coreason_client import CAPClient, ServiceRequest
from coreason_manifest.definitions.session import SessionContext
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.message import ChatMessage
from coreason_manifest.definitions.presentation import StreamOpCode

client = CAPClient(base_url="...", api_key="...")

# 1. Manually construct the envelope
context = SessionContext(
    user_id="user_123",
    session_id="sess_abc",
    # ... other required fields
)

payload = AgentRequest(
    messages=[
        ChatMessage.user("Analyze this data."),
        # ... attached files or complex history
    ]
)

request = ServiceRequest(
    request_id=uuid4(),
    context=context,
    payload=payload
)

# 2. Iterate strictly over packets
for packet in client.assist(request):
    if packet.op == StreamOpCode.DELTA:
        print(packet.p, end="")
    elif packet.op == StreamOpCode.EVENT:
        event = packet.p
        if event['type'] == 'CITATION_BLOCK':
            print(f"\n[Citation: {event['data']['citations'][0]['uri']}]")
```

## 5. Error Handling Taxonomy

The client maps all failures into a strict hierarchy of exceptions to allow deterministic error handling by the consumer.

*   **`CAPError`** (Base Class)
    *   **`CAPConnectionError`**: The client could not establish or maintain a connection after exhausting all retry attempts.
        *   *Cause:* Internet down, DNS failure, Server down.
        *   *Action:* User should check network or try again later.
    *   **`CAPProtocolError`**: The server responded with data that violates the wire protocol.
        *   *Cause:* Malformed JSON, missing fields in `StreamPacket`, unknown OpCode.
        *   *Action:* Developer should check SDK version compatibility or report bug.
    *   **`CAPRuntimeError`**: The server received the request but rejected it or failed during processing.
        *   *Cause:* 401 Unauthorized, 429 Rate Limit, 500 Internal Error, or an explicit `op=ERROR` packet in the stream.
        *   *Action:* Handle based on the specific HTTP status code or error message attached.
