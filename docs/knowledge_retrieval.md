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

### 3. Retrieval Configuration

The `RetrievalConfig` model encapsulates the RAG parameters.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `strategy` | `RetrievalStrategy` | `HYBRID` | The search algorithm to use. |
| `collection_name` | `str` | **Required** | The ID of the vector/graph collection to query. |
| `top_k` | `int` | `5` | Number of chunks/nodes to retrieve (must be >= 1). |
| `score_threshold` | `float` | `0.7` | Minimum similarity score (0.0 - 1.0) to consider a match. |
| `scope` | `KnowledgeScope` | `SHARED` | Access control boundary. |

## Integration with Cognitive Profile

The `CognitiveProfile` (in `coreason_manifest.spec.v2.agent`) now includes a `memory` field, which is a list of `RetrievalConfig` objects. This allows an agent to query multiple knowledge sources simultaneously.

### Example: Hybrid RAG Setup

```python
from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.knowledge import (
    RetrievalConfig,
    RetrievalStrategy,
    KnowledgeScope
)

# Define an agent with access to legal precedents and user notes
legal_expert = CognitiveProfile(
    role="legal_analyst",
    memory=[
        # 1. Access Shared Legal Precedents (Vector Search)
        RetrievalConfig(
            strategy=RetrievalStrategy.DENSE,
            collection_name="supreme_court_cases",
            top_k=3,
            score_threshold=0.85,
            scope=KnowledgeScope.SHARED
        ),
        # 2. Access Private Case Notes (Keyword Search)
        RetrievalConfig(
            strategy=RetrievalStrategy.SPARSE,
            collection_name="case_notes",
            top_k=5,
            scope=KnowledgeScope.USER
        )
    ]
)
```

This configuration tells the runtime to:
1.  Perform a vector search on the "supreme_court_cases" collection.
2.  Perform a keyword search on the user's "case_notes".
3.  Combine and inject the retrieved context into the agent's prompt.
