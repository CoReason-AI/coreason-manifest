import pytest
from pydantic import ValidationError

from coreason_manifest.core.primitives.types import RiskLevel
from coreason_manifest.core.state.memory import KnowledgeScope, RetrievalStrategy, SemanticMemoryConfig
from coreason_manifest.core.state.tools import LoadStrategy, ToolCapability


def test_tool_eager_load_strategy_success() -> None:
    """Test that an EAGER tool without trigger_intent parses successfully."""
    tool = ToolCapability(
        name="calculator",
        risk_level=RiskLevel.STANDARD,
        description="A calculator tool",
        load_strategy=LoadStrategy.EAGER,
        trigger_intent=None,
    )
    assert tool.load_strategy == LoadStrategy.EAGER
    assert tool.trigger_intent is None


def test_tool_lazy_load_strategy_success() -> None:
    """Test that a LAZY tool with a valid trigger_intent parses successfully."""
    tool = ToolCapability(
        name="patient_data_extractor",
        risk_level=RiskLevel.STANDARD,
        description="Extracts data",
        load_strategy=LoadStrategy.LAZY,
        trigger_intent="Extract patient phenotypes from unstructured clinical notes",
    )
    assert tool.load_strategy == LoadStrategy.LAZY
    assert tool.trigger_intent == "Extract patient phenotypes from unstructured clinical notes"


def test_tool_lazy_load_strategy_missing_intent_fails() -> None:
    """Test that a LAZY tool without a valid trigger_intent raises ValidationError."""
    match_msg = "A valid, non-empty 'trigger_intent' is required for vector discovery when load_strategy is LAZY."

    with pytest.raises(ValidationError, match=match_msg):
        ToolCapability(
            name="patient_data_extractor",
            risk_level=RiskLevel.STANDARD,
            description="Extracts data",
            load_strategy=LoadStrategy.LAZY,
            trigger_intent=None,
        )

    with pytest.raises(ValidationError, match=match_msg):
        ToolCapability(
            name="patient_data_extractor",
            risk_level=RiskLevel.STANDARD,
            description="Extracts data",
            load_strategy=LoadStrategy.LAZY,
            trigger_intent="",
        )

    with pytest.raises(ValidationError, match=match_msg):
        ToolCapability(
            name="patient_data_extractor",
            risk_level=RiskLevel.STANDARD,
            description="Extracts data",
            load_strategy=LoadStrategy.LAZY,
            trigger_intent="   ",
        )


def test_semantic_memory_config_missing_scope_fails() -> None:
    """Test that SemanticMemoryConfig raises ValidationError if scope is not explicitly provided."""
    with pytest.raises(ValidationError, match="Field required"):
        SemanticMemoryConfig.model_validate(
            {
                "graph_namespace": "test_namespace",
                "bitemporal_tracking": True,
                "retrieval_strategy": "graph_rag",
                "min_score_threshold": 0.8,
            }
        )


def test_semantic_memory_config_valid_fields() -> None:
    """Test that SemanticMemoryConfig serializes RetrievalStrategy.GRAPH_RAG correctly."""
    config = SemanticMemoryConfig(
        graph_namespace="test_namespace",
        bitemporal_tracking=True,
        retrieval_strategy=RetrievalStrategy.GRAPH_RAG,
        scope=KnowledgeScope.SESSION,
        min_score_threshold=0.8,
    )
    assert config.retrieval_strategy == RetrievalStrategy.GRAPH_RAG
    assert config.scope == KnowledgeScope.SESSION
    assert config.min_score_threshold == 0.8


def test_semantic_memory_config_invalid_threshold_fails() -> None:
    """Test that SemanticMemoryConfig rejects invalid float values for min_score_threshold."""
    with pytest.raises(ValidationError):
        SemanticMemoryConfig(
            graph_namespace="test_namespace",
            bitemporal_tracking=True,
            retrieval_strategy=RetrievalStrategy.GRAPH_RAG,
            scope=KnowledgeScope.SESSION,
            min_score_threshold=1.5,
        )

    with pytest.raises(ValidationError):
        SemanticMemoryConfig(
            graph_namespace="test_namespace",
            bitemporal_tracking=True,
            retrieval_strategy=RetrievalStrategy.GRAPH_RAG,
            scope=KnowledgeScope.SESSION,
            min_score_threshold=-0.1,
        )
