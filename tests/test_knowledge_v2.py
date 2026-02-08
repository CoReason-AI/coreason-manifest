# tests/test_knowledge_v2.py

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.knowledge import KnowledgeScope, RetrievalConfig, RetrievalStrategy
from coreason_manifest.spec.v2.recipe import AgentNode, GraphTopology, RecipeDefinition, RecipeInterface, RecipeStatus


def test_retrieval_config_valid() -> None:
    config = RetrievalConfig(
        strategy=RetrievalStrategy.HYBRID,
        collection_name="test_collection",
        top_k=10,
        score_threshold=0.8,
        scope=KnowledgeScope.SHARED
    )
    assert config.strategy == "hybrid"
    assert config.collection_name == "test_collection"
    assert config.top_k == 10
    assert config.score_threshold == 0.8
    assert config.scope == "shared"

def test_retrieval_config_defaults() -> None:
    config = RetrievalConfig(collection_name="simple")
    assert config.strategy == RetrievalStrategy.HYBRID
    assert config.top_k == 5
    assert config.score_threshold == 0.7
    assert config.scope == KnowledgeScope.SHARED

def test_retrieval_config_invalid_score() -> None:
    with pytest.raises(ValidationError):
        RetrievalConfig(collection_name="test", score_threshold=1.1)

    with pytest.raises(ValidationError):
        RetrievalConfig(collection_name="test", score_threshold=-0.1)

def test_retrieval_config_invalid_top_k() -> None:
    with pytest.raises(ValidationError):
        RetrievalConfig(collection_name="test", top_k=0)

def test_cognitive_profile_with_memory() -> None:
    mem_config = RetrievalConfig(collection_name="legal_docs", strategy="dense")
    profile = CognitiveProfile(
        role="Legal Advisor",
        reasoning_mode="react",
        memory=[mem_config],
        knowledge_contexts=["ctx_1"],
        task_primitive="analyze"
    )
    assert profile.role == "Legal Advisor"
    assert len(profile.memory) == 1
    assert profile.memory[0].strategy == "dense"

def test_agent_node_construct() -> None:
    profile = CognitiveProfile(
        role="Analyst",
        reasoning_mode="cot"
    )
    node = AgentNode(
        id="agent_1",
        agent_ref="agent_def_1",
        construct=profile
    )
    assert node.construct is not None
    assert node.construct.role == "Analyst"

def test_full_recipe_with_knowledge() -> None:
    # Construct a full recipe with an inline agent using knowledge
    rag_config = RetrievalConfig(
        strategy=RetrievalStrategy.GRAPH_RAG,
        collection_name="enterprise_graph",
        top_k=20,
        scope=KnowledgeScope.SHARED
    )

    profile = CognitiveProfile(
        role="Graph Analyst",
        reasoning_mode="cot",
        memory=[rag_config]
    )

    agent_node = AgentNode(
        id="step-1",
        agent_ref="base-agent", # Fallback or base
        construct=profile
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="RAG Recipe"),
        interface=RecipeInterface(),
        status=RecipeStatus.DRAFT,
        topology=GraphTopology(
            nodes=[agent_node],
            edges=[],
            entry_point="step-1"
        )
    )

    assert len(recipe.topology.nodes) == 1
    node = recipe.topology.nodes[0]
    assert isinstance(node, AgentNode)
    assert node.construct is not None
    assert node.construct.memory[0].strategy == "graph_rag"

def test_serialization() -> None:
    config = RetrievalConfig(collection_name="test")
    dump = config.model_dump()
    assert dump["collection_name"] == "test"
    assert dump["strategy"] == "hybrid"

    profile = CognitiveProfile(role="tester", reasoning_mode="test", memory=[config])
    dump_p = profile.model_dump()
    assert dump_p["memory"][0]["collection_name"] == "test"
