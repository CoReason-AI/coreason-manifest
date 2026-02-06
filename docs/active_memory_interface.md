# Active Memory Interface

The **Active Memory Interface** defines the contract for agents to actively interact with their storage backend (e.g., Redis, Postgres) during execution. While `SessionState` manages the passive, immutable state passed between turns, the `SessionHandle` protocol allows agents to perform I/O operations like semantic search ("recall"), history retrieval, and persistent variable storage.

## The `SessionHandle` Protocol

The `SessionHandle` is a strictly typed `typing.Protocol` decorated with `@runtime_checkable`. It decouples the agent's reasoning logic from the underlying infrastructure.

### Definition

```python
@runtime_checkable
class SessionHandle(Protocol):
    """Protocol defining the interface for active memory interaction."""

    @property
    def session_id(self) -> str:
        """The unique session identifier."""
        ...

    @property
    def identity(self) -> Identity:
        """The identity of the user/owner."""
        ...

    async def history(self, limit: int = 10, offset: int = 0) -> list[Interaction]:
        """Fetch recent conversation turns."""
        ...

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[str]:
        """Perform semantic search (RAG) over the knowledge base."""
        ...

    async def store(self, key: str, value: Any) -> None:
        """Persist a variable across turns."""
        ...

    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a persisted variable."""
        ...
```

### Methods

| Method | Description | Signature |
| :--- | :--- | :--- |
| `history` | Fetches recent conversation interactions. | `async def history(limit: int, offset: int) -> list[Interaction]` |
| `recall` | Performs semantic search (RAG) to retrieve relevant knowledge. | `async def recall(query: str, limit: int, threshold: float) -> list[str]` |
| `store` | Persists an arbitrary value associated with a key. | `async def store(key: str, value: Any) -> None` |
| `get` | Retrieves a persisted value by key. | `async def get(key: str, default: Any) -> Any` |

### Usage

Agents receive a `SessionHandle` at runtime. They can use it to augment their context before generating a response.

```python
async def my_agent_logic(session: SessionHandle, user_input: str):
    # 1. Recall relevant facts
    facts = await session.recall(user_input)

    # 2. Retrieve user preferences
    style = await session.get("response_style", "concise")

    # 3. Process...
    response = generate_response(user_input, facts, style)

    # 4. Store new preference if detected
    if "speak verbose" in user_input:
        await session.store("response_style", "verbose")

    return response
```
