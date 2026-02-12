from pydantic import TypeAdapter

from coreason_manifest.spec.core.engines import (
    GraphReasoning,
    ModelCriteria,
    ReasoningConfig,
)


def test_graph_reasoning_instantiation() -> None:
    # Test defaults
    graph = GraphReasoning(model="gpt-4", graph_store="neo4j-prod")
    assert graph.type == "graph"
    assert graph.retrieval_mode == "local"
    assert graph.max_hops == 2
    assert graph.community_level == 1
    assert graph.extraction_model is None

    # Test with custom fields
    criteria = ModelCriteria(strategy="performance")
    graph_custom = GraphReasoning(
        model="gpt-4-turbo",
        graph_store="memory://test",
        retrieval_mode="global",
        extraction_model=criteria,
        max_hops=3,
        community_level=2,
    )
    assert graph_custom.graph_store == "memory://test"
    assert graph_custom.retrieval_mode == "global"
    assert isinstance(graph_custom.extraction_model, ModelCriteria)
    assert graph_custom.extraction_model.strategy == "performance"
    assert graph_custom.max_hops == 3
    assert graph_custom.community_level == 2


def test_reasoning_config_union_graph_rag() -> None:
    # Use TypeAdapter to test parsing into the Union
    adapter: TypeAdapter[ReasoningConfig] = TypeAdapter(ReasoningConfig)

    data = {
        "type": "graph",
        "model": "gpt-4",
        "graph_store": "neo4j://localhost:7687",
        "retrieval_mode": "hybrid",
    }
    parsed = adapter.validate_python(data)
    assert isinstance(parsed, GraphReasoning)
    assert parsed.type == "graph"
    assert parsed.graph_store == "neo4j://localhost:7687"
    assert parsed.retrieval_mode == "hybrid"
