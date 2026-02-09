# Knowledge Retrieval & Long-Term Memory (RAG)

The **Knowledge & Retrieval Schema** (`coreason_manifest.spec.v2.knowledge`) defines how an agent accesses long-term memory. It allows a `Recipe` to strictly configure Retrieval-Augmented Generation (RAG) capabilities, supporting vector search, keyword search, and knowledge graph traversal.

## Core Concepts

### 1. Retrieval Strategy

The `RetrievalStrategy` defines the algorithm used to fetch relevant context from the archive.

*   `DENSE` (`"dense"`): Vector similarity search (semantic match).
*   `SPARSE` (`"sparse"`): Keyword/BM25 search (exact term match).
*   `HYBRID` (`"hybrid"`): A combination of Dense and Sparse search, typically re-ranked using Reciprocal Rank Fusion (RRF). This is the default.
*   `GRAPH` (`"graph"`): Knowledge Graph traversal (following semantic links).
*   `GRAPH_RAG` (`"graph_rag"`): A hybrid approach combining vector search with graph exploration.

### 2. Knowledge Scope

The `KnowledgeScope` defines the boundary of memory access, ensuring data privacy and relevance.

*   `SHARED` (`"shared"`): Global organization knowledge, accessible to all users.
*   `USER` (`"user"`): User-specific private memory (e.g., personal documents).
*   `SESSION` (`"session"`): Ephemeral context limited to the current conversation/session.

### 3. Retrieval Configuration (Read)

The `RetrievalConfig` model encapsulates the RAG parameters.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `strategy` | `RetrievalStrategy` | `HYBRID` | The search algorithm to use. |
| `collection_name` | `str` | **Required** | The ID of the vector/graph collection to query. |
| `top_k` | `int` | `5` | Number of chunks/nodes to retrieve (must be >= 1). |
| `score_threshold` | `float` | `0.7` | Minimum similarity score (0.0 - 1.0) to consider a match. |
| `scope` | `KnowledgeScope` | `SHARED` | Access control boundary. |

### 4. Memory Consolidation (Write)

The `MemoryWriteConfig` defines how short-term conversation history is summarized and written to long-term vector storage (Crystallization).

#### Consolidation Strategy

*   `NONE` (`"none"`): Forget everything after session.
*   `SUMMARY_WINDOW` (`"summary_window"`): Summarize every N turns.
*   `SEMANTIC_CLUSTER` (`"semantic_cluster"`): Group related turns by topic.
*   `SESSION_CLOSE` (`"session_close"`): Crystallize only when session ends.

#### Write Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `strategy` | `ConsolidationStrategy` | `SESSION_CLOSE` | When to persist memories. |
| `frequency_turns` | `int` | `10` | Turns trigger for `SUMMARY_WINDOW`. |
| `destination_collection` | `str` | `None` | Target collection. If `None`, uses primary read collection. |

## Integration with Cognitive Profile

The `CognitiveProfile` (in `coreason_manifest.spec.v2.agent`) includes:
*   `memory_read` (aliased as `memory`): A list of `RetrievalConfig` objects.
*   `memory_write`: A `MemoryWriteConfig` object.

### Example: Hybrid RAG & Consolidation

```python
from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.knowledge import (
    RetrievalConfig,
    RetrievalStrategy,
    KnowledgeScope,
    MemoryWriteConfig,
    ConsolidationStrategy
)

# Define an agent with access to legal precedents and user notes
legal_expert = CognitiveProfile(
    role="legal_analyst",

    # Read from multiple sources
    memory=[
        RetrievalConfig(
            strategy=RetrievalStrategy.DENSE,
            collection_name="supreme_court_cases",
            top_k=3,
            score_threshold=0.85,
            scope=KnowledgeScope.SHARED
        ),
        RetrievalConfig(
            strategy=RetrievalStrategy.SPARSE,
            collection_name="case_notes",
            top_k=5,
            scope=KnowledgeScope.USER
        )
    ],

    # Write summary back to user notes at session end
    memory_write=MemoryWriteConfig(
        strategy=ConsolidationStrategy.SESSION_CLOSE,
        destination_collection="case_notes"
    )
)
```
