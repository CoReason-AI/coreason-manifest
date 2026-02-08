# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.agent import CognitiveProfile, ComponentPriority, ContextDependency
from coreason_manifest.spec.v2.knowledge import (
    ConsolidationStrategy,
    KnowledgeScope,
    MemoryWriteConfig,
    RetrievalConfig,
    RetrievalStrategy,
)
from coreason_manifest.spec.v2.reasoning import (
    AdversarialConfig,
    GapScanConfig,
    ReasoningConfig,
    ReflexConfig,
    ReviewStrategy,
)


def test_full_cognitive_profile_integration() -> None:
    """Test creating a complex CognitiveProfile with all new features enabled."""

    # 1. Configure Reflex (System 1)
    reflex = ReflexConfig(
        enabled=True,
        confidence_threshold=0.95,
        allowed_tools=["calculator", "get_time"],
    )

    # 2. Configure Episteme (System 2)
    episteme = ReasoningConfig(
        strategy=ReviewStrategy.ADVERSARIAL,
        adversarial=AdversarialConfig(
            persona="security_auditor",
            attack_vectors=["prompt_injection", "pii_leakage"],
            temperature=0.4,
        ),
        gap_scan=GapScanConfig(
            enabled=True,
            confidence_threshold=0.8,
        ),
        max_revisions=3,
    )

    # 3. Configure RAG (Memory Read)
    read_configs = [
        RetrievalConfig(
            strategy=RetrievalStrategy.HYBRID,
            collection_name="global_knowledge",
            scope=KnowledgeScope.SHARED,
            top_k=5,
        ),
        RetrievalConfig(
            strategy=RetrievalStrategy.DENSE,
            collection_name="user_notes",
            scope=KnowledgeScope.USER,
            top_k=10,
        ),
    ]

    # 4. Configure Memory Consolidation (Memory Write)
    write_config = MemoryWriteConfig(
        strategy=ConsolidationStrategy.SEMANTIC_CLUSTER,
        frequency_turns=5,
        destination_collection="consolidated_memory",
    )

    # 5. Assemble Profile
    profile = CognitiveProfile(
        role="senior_analyst",
        reasoning_mode="analytical",
        knowledge_contexts=[
            ContextDependency(name="policy_docs", priority=ComponentPriority.HIGH),
        ],
        reflex=reflex,
        reasoning=episteme,
        memory_read=read_configs,
        memory_write=write_config,
        task_primitive="analyze_data",
    )

    # Assertions
    assert profile.reflex == reflex
    assert profile.reasoning == episteme
    assert profile.memory_read == read_configs
    # Check alias access
    assert profile.memory == read_configs
    assert profile.memory_write == write_config

    # Verify serialization
    dumped = profile.model_dump(by_alias=True)
    assert dumped["reflex"]["confidence_threshold"] == 0.95
    assert dumped["reasoning"]["strategy"] == "adversarial"
    assert dumped["memory"][0]["collection_name"] == "global_knowledge"
    assert dumped["memory_write"]["strategy"] == "semantic_cluster"


def test_overlapping_memory_configuration() -> None:
    """Test overlapping configurations to ensure no conflict."""
    # It is valid to have read/write pointing to same or different collections
    profile = CognitiveProfile(
        role="clerk",
        memory_read=[RetrievalConfig(collection_name="inbox", scope=KnowledgeScope.SESSION)],
        memory_write=MemoryWriteConfig(
            strategy=ConsolidationStrategy.SESSION_CLOSE,
            destination_collection="archive",  # Different from read
        ),
    )

    assert profile.memory_read[0].collection_name == "inbox"
    assert profile.memory_write is not None
    assert profile.memory_write.destination_collection == "archive"

    # Same collection for read/write (also valid logic)
    profile_same = CognitiveProfile(
        role="librarian",
        memory_read=[RetrievalConfig(collection_name="library", scope=KnowledgeScope.SHARED)],
        memory_write=MemoryWriteConfig(
            strategy=ConsolidationStrategy.SUMMARY_WINDOW,
            destination_collection="library",  # Same as read
        ),
    )
    assert profile_same.memory_read[0].collection_name == "library"
    assert profile_same.memory_write is not None
    assert profile_same.memory_write.destination_collection == "library"
