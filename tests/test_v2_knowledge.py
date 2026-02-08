# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.knowledge import (
    KnowledgeScope,
    RetrievalConfig,
    RetrievalStrategy,
)


def test_retrieval_strategy_enum() -> None:
    """Ensure RetrievalStrategy values are correct."""
    assert RetrievalStrategy.DENSE == "dense"
    assert RetrievalStrategy.SPARSE == "sparse"
    assert RetrievalStrategy.HYBRID == "hybrid"
    assert RetrievalStrategy.GRAPH == "graph"
    assert RetrievalStrategy.GRAPH_RAG == "graph_rag"


def test_knowledge_scope_enum() -> None:
    """Ensure KnowledgeScope values are correct."""
    assert KnowledgeScope.SHARED == "shared"
    assert KnowledgeScope.USER == "user"
    assert KnowledgeScope.SESSION == "session"


def test_retrieval_config_defaults() -> None:
    """Test defaults for RetrievalConfig."""
    config = RetrievalConfig(collection_name="test_collection")
    assert config.strategy == RetrievalStrategy.HYBRID
    assert config.top_k == 5
    assert config.score_threshold == 0.7
    assert config.scope == KnowledgeScope.SHARED
    assert config.collection_name == "test_collection"


def test_retrieval_config_custom() -> None:
    """Test custom values for RetrievalConfig."""
    config = RetrievalConfig(
        strategy=RetrievalStrategy.GRAPH,
        collection_name="legal_docs",
        top_k=10,
        score_threshold=0.5,
        scope=KnowledgeScope.USER,
    )
    assert config.strategy == RetrievalStrategy.GRAPH
    assert config.collection_name == "legal_docs"
    assert config.top_k == 10
    assert config.score_threshold == 0.5
    assert config.scope == KnowledgeScope.USER


def test_retrieval_config_validation() -> None:
    """Test validation constraints."""
    # Test top_k < 1
    with pytest.raises(ValidationError) as exc:
        RetrievalConfig(collection_name="test", top_k=0)
    assert "Input should be greater than or equal to 1" in str(exc.value)

    # Test score_threshold < 0
    with pytest.raises(ValidationError) as exc:
        RetrievalConfig(collection_name="test", score_threshold=-0.1)
    assert "Input should be greater than or equal to 0" in str(exc.value)

    # Test score_threshold > 1
    with pytest.raises(ValidationError) as exc:
        RetrievalConfig(collection_name="test", score_threshold=1.1)
    assert "Input should be less than or equal to 1" in str(exc.value)


def test_cognitive_profile_with_memory() -> None:
    """Test integration of RetrievalConfig into CognitiveProfile."""
    memory_config = RetrievalConfig(
        strategy=RetrievalStrategy.DENSE, collection_name="history"
    )
    profile = CognitiveProfile(
        role="archivist",
        memory=[memory_config],
    )
    assert len(profile.memory) == 1
    assert profile.memory[0].collection_name == "history"
    assert profile.memory[0].strategy == RetrievalStrategy.DENSE


def test_serialization() -> None:
    """Test serialization of RetrievalConfig."""
    config = RetrievalConfig(collection_name="test", top_k=3)
    dumped = config.dump()
    assert dumped["collection_name"] == "test"
    assert dumped["top_k"] == 3
    assert dumped["strategy"] == "hybrid"  # Default
