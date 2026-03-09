from coreason_manifest.compute.test_time import SubstrateEnvelope


def test_substrate_envelope_valid_instantiation() -> None:
    """Assert the declarative schema accepts strictly positive economic bounds."""
    envelope = SubstrateEnvelope(
        algorithmic_token_budget=100000,
        vram_frontier_bound=8589934592,  # 8GB
        latency_sla_ms=5000,
        probabilistic_exhaustion_halt=True,
    )
    assert envelope.algorithmic_token_budget == 100000
    assert envelope.probabilistic_exhaustion_halt is True
