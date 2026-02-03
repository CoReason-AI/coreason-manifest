# Active Memory Interface

The **Active Memory Interface** (`SessionHandle`) is the standardized protocol by which a running Agent interacts with its environment, specifically regarding conversation history, long-term persistence, and semantic search (RAG).

Unlike passive `SessionState`, which acts as a data container, the `SessionHandle` provides an active API for the Agent to "pull" information on demand.

## Motivation

Traditionally, agents receive their entire conversation history as a static list of messages in the input prompt. This has two major drawbacks:

1.  **Inefficiency:** As conversations grow, the context window fills up with potentially irrelevant data, increasing latency and cost.
2.  **Lack of Agency:** The agent cannot decide *what* it needs to remember or search for; it is spoon-fed a fixed context.

The `SessionHandle` solves this by giving the agent tools to manage its own context.

## The `SessionHandle` Protocol

Defined in `src/coreason_manifest/definitions/interfaces.py`:

```python
@runtime_checkable
class SessionHandle(Protocol):
    @property
    def session_id(self) -> str: ...

    @property
    def identity(self) -> Identity: ...

    async def history(self, limit: int = 10, offset: int = 0) -> List[Interaction]:
        """Fetch recent conversation turns."""
        ...

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> List[str]:
        """Perform semantic search (RAG) over the knowledge base."""
        ...

    async def store(self, key: str, value: Any) -> None:
        """Persist a variable across turns."""
        ...

    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a persisted variable."""
        ...
```

## Key Capabilities

### 1. Lazy History Loading
Agents can request only the most recent $N$ interactions, rather than loading the full history.

```python
# Get only the last 5 turns
recent_turns = await session.history(limit=5)
```

### 2. Retrieval Augmented Generation (RAG)
The `recall()` method abstracts away the underlying Vector Database. The Agent simply expresses a semantic query, and the Runtime resolves it against the configured knowledge base.

```python
# Semantic search
relevant_docs = await session.recall("What is the refund policy for subscriptions?")
```

### 3. Long-Term Persistence (KV Store)
Agents can store variables that persist across the entire session lifecycle, independent of the conversation window.

```python
# Store user preference
await session.store("preferred_language", "es")

# Retrieve later
lang = await session.get("preferred_language", "en")
```

## Usage Example

```python
async def assist(self, request: AgentRequest, session: SessionHandle, response: ResponseHandler) -> None:
    # 1. Check if we know the user's name
    user_name = await session.get("user_name")

    # 2. If not, maybe check history
    if not user_name:
        history = await session.history(limit=5)
        # ... logic to extract name from history ...

    # 3. Use RAG if the user asks a specific question
    if "policy" in request.payload.get("query", ""):
        docs = await session.recall("policy documents")
        await response.thought(f"Found {len(docs)} relevant documents.")

    # ...
```
