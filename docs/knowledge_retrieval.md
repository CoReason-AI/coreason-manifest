# Knowledge Schema & Retrieval

The Coreason Manifest V2 introduces explicit support for **Knowledge Requirements** via the `RetrievalConfig` schema. This allows agents to declare their need for long-term memory access, enabling Retrieval-Augmented Generation (RAG) capabilities.

## Overview

Agents can now be configured with one or more `RetrievalConfig` entries within their `CognitiveProfile`. This configuration dictates how the runtime should access vector stores, knowledge graphs, or other search indices.

## Retrieval Configuration

The `RetrievalConfig` model defines the strategy, target collection, and parameters for retrieval.

### Schema

```python
class RetrievalConfig(CoReasonBaseModel):
    strategy: RetrievalStrategy = Field(RetrievalStrategy.HYBRID, description="Search algorithm.")
    collection_name: str = Field(..., description="The ID of the vector/graph collection to query.")
    top_k: int = Field(5, ge=1, description="Number of chunks to retrieve.")
    score_threshold: float | None = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score.")
    scope: KnowledgeScope = Field(KnowledgeScope.SHARED, description="Access control scope.")
```

### Retrieval Strategies

The `RetrievalStrategy` enum defines the available search algorithms:

*   **`DENSE`**: Vector similarity search (semantic search). Best for understanding intent.
*   **`SPARSE`**: Keyword/BM25 search. Best for exact match or jargon.
*   **`HYBRID`**: Combination of Dense + Sparse with Reciprocal Rank Fusion (RRF). Generally provides the best recall.
*   **`GRAPH`**: Knowledge Graph traversal. Useful for structured relationships.
*   **`GRAPH_RAG`**: Hybrid approach combining Vector search with Knowledge Graph context.

### Knowledge Scopes

The `KnowledgeScope` enum defines the boundary of access:

*   **`SHARED`**: Global organization knowledge. Accessible by all agents with permission.
*   **`USER`**: User-specific private memory. Only accessible when executing on behalf of a specific user.
*   **`SESSION`**: Ephemeral conversation context. Cleared after the session ends.

## Usage in Cognitive Profile

To equip an agent with RAG capabilities, add `RetrievalConfig` entries to the `memory` field of its `CognitiveProfile`.

```yaml
nodes:
  - id: "research_agent"
    type: "agent"
    construct:
      role: "Researcher"
      reasoning_mode: "react"
      memory:
        - strategy: "hybrid"
          collection_name: "legal_precedents"
          top_k: 10
          score_threshold: 0.8
          scope: "shared"
```

This configuration instructs the runtime to perform a hybrid search on the "legal_precedents" collection whenever the agent needs to retrieve information.
