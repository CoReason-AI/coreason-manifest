from coreason_manifest.builder import AgentBuilder
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile


def test_agent_builder_with_memory_full_config() -> None:
    """Test with_memory with all parameters provided."""
    builder = AgentBuilder("test_agent")
    builder.with_identity("Assistant", "Helper")
    builder.with_memory(
        working_limit=8192,
        enable_paging=True,
        salience_threshold=0.8,
        consolidation_interval=10,
        graph_namespace="test_graph",
        bitemporal_tracking=True,
        allowed_entity_types=["user", "product"],
        skill_library_ref="global_skills",
    )

    agent = builder.build()

    assert isinstance(agent.profile, CognitiveProfile)
    assert agent.profile.memory is not None
    assert agent.profile.memory.working is not None
    assert agent.profile.memory.working.max_tokens == 8192
    assert agent.profile.memory.working.enable_active_paging is True

    assert agent.profile.memory.episodic is not None
    assert agent.profile.memory.episodic.salience_threshold == 0.8
    assert agent.profile.memory.episodic.consolidation_interval_turns == 10

    assert agent.profile.memory.semantic is not None
    assert agent.profile.memory.semantic.graph_namespace == "test_graph"
    assert agent.profile.memory.semantic.bitemporal_tracking is True
    assert agent.profile.memory.semantic.allowed_entity_types == ["user", "product"]

    assert agent.profile.memory.procedural is not None
    assert agent.profile.memory.procedural.skill_library_ref == "global_skills"


def test_agent_builder_with_memory_minimal_config() -> None:
    """Test with_memory with minimal/default parameters."""
    builder = AgentBuilder("test_agent_min")
    builder.with_identity("Assistant", "Helper")
    builder.with_memory(working_limit=4096)

    agent = builder.build()

    assert isinstance(agent.profile, CognitiveProfile)
    assert agent.profile.memory is not None
    assert agent.profile.memory.working is not None
    assert agent.profile.memory.working.max_tokens == 4096
    # Check default arguments behavior
    assert agent.profile.memory.working.enable_active_paging is False

    # Optional sections should be None if not provided
    assert agent.profile.memory.episodic is None
    assert agent.profile.memory.semantic is None
    assert agent.profile.memory.procedural is None


def test_agent_builder_with_memory_partial_config() -> None:
    """Test with_memory with some optional parameters to hit different branches."""
    builder = AgentBuilder("test_agent_partial")
    builder.with_identity("Assistant", "Helper")

    # Provide episodic but not semantic or procedural
    builder.with_memory(salience_threshold=0.5)

    agent = builder.build()
    assert isinstance(agent.profile, CognitiveProfile)
    assert agent.profile.memory is not None
    assert agent.profile.memory.episodic is not None
    assert agent.profile.memory.episodic.salience_threshold == 0.5
    assert agent.profile.memory.episodic.consolidation_interval_turns is None
    assert agent.profile.memory.semantic is None
    assert agent.profile.memory.procedural is None

    # New builder for semantic only
    builder2 = AgentBuilder("test_agent_partial_2")
    builder2.with_identity("Assistant", "Helper")
    builder2.with_memory(graph_namespace="kb")
    agent2 = builder2.build()
    assert isinstance(agent2.profile, CognitiveProfile)
    assert agent2.profile.memory is not None
    assert agent2.profile.memory.semantic is not None
    assert agent2.profile.memory.semantic.graph_namespace == "kb"
    assert agent2.profile.memory.episodic is None

    # New builder for procedural only
    builder3 = AgentBuilder("test_agent_partial_3")
    builder3.with_identity("Assistant", "Helper")
    builder3.with_memory(skill_library_ref="libs")
    agent3 = builder3.build()
    assert isinstance(agent3.profile, CognitiveProfile)
    assert agent3.profile.memory is not None
    assert agent3.profile.memory.procedural is not None
    assert agent3.profile.memory.procedural.skill_library_ref == "libs"
