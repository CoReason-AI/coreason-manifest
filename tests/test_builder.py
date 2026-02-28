from coreason_manifest.core.oversight.governance import RequestCriticality
from coreason_manifest.toolkit.builder import AgentBuilder, NewLinearFlow


def test_agent_builder_traffic_policy() -> None:
    builder = AgentBuilder("test_agent").with_identity("Test", "Test persona")

    # Test only rpm setting (semantic cache should be default)
    builder.with_operational_policy(rate_limit_rpm=100)
    agent = builder.build()

    assert agent.operational_policy is not None
    assert agent.operational_policy.traffic is not None
    assert agent.operational_policy.traffic.rate_limit_rpm == 100
    assert agent.operational_policy.traffic.semantic_cache is not None
    assert agent.operational_policy.traffic.semantic_cache.enabled is True

    # Test setting cache values explicitly
    builder.with_operational_policy(rate_limit_tpm=5000, semantic_cache_similarity=0.9, semantic_cache_ttl=1800)
    agent2 = builder.build()

    assert agent2.operational_policy is not None
    assert agent2.operational_policy.traffic is not None
    assert agent2.operational_policy.traffic.rate_limit_tpm == 5000
    assert agent2.operational_policy.traffic.semantic_cache is not None
    assert agent2.operational_policy.traffic.semantic_cache.similarity_threshold == 0.9
    assert agent2.operational_policy.traffic.semantic_cache.ttl_seconds == 1800


def test_flow_builder_traffic_policy() -> None:
    builder = NewLinearFlow("test_flow", "0.1.0", "Test Flow")

    # Test criticality and caching
    builder.set_operational_policy(
        criticality=RequestCriticality.CRITICAL, rate_limit_tpm=20000, semantic_cache_ttl=7200
    )

    agent = AgentBuilder("test_agent").with_identity("Test", "Test persona").build()
    builder.add_agent(agent)
    flow = builder.build()

    assert flow.governance is not None
    assert flow.governance.operational_policy is not None
    assert flow.governance.operational_policy.traffic is not None
    assert flow.governance.operational_policy.traffic.criticality == RequestCriticality.CRITICAL
    assert flow.governance.operational_policy.traffic.rate_limit_tpm == 20000
    assert flow.governance.operational_policy.traffic.semantic_cache is not None
    assert flow.governance.operational_policy.traffic.semantic_cache.ttl_seconds == 7200
