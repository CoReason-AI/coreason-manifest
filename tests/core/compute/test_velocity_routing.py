import pytest

from coreason_manifest.core.compute.resources import IntentRouter, provision_compute
from coreason_manifest.core.compute.velocity import (
    ComputeIntent,
    VelocityAConfig,
    VelocityBConfig,
)
from coreason_manifest.core.workflow.exceptions import LatencySLAExceededError


@pytest.mark.asyncio
async def test_realtime_sync_routing() -> None:
    """Test 1: Prove that REALTIME_SYNC correctly returns VelocityAConfig."""
    config = await provision_compute(intent=ComputeIntent.REALTIME_SYNC, task_def={})
    assert isinstance(config, VelocityAConfig)
    assert config.allow_model_downgrade is True
    assert config.max_latency_seconds == 60
    assert config.target_compute_tier == "serverless_burst"


@pytest.mark.asyncio
async def test_batch_background_routing() -> None:
    """Extra Test: Prove that BATCH_BACKGROUND correctly returns VelocityBConfig."""
    config = await provision_compute(intent=ComputeIntent.BATCH_BACKGROUND, task_def={})
    assert isinstance(config, VelocityBConfig)
    assert config.preemption_safe is True
    assert config.max_retries == -1
    assert config.target_compute_tier == "spot_fleet"


def test_intent_router_invalid_intent() -> None:
    """Test router raising error on invalid intent."""
    router = IntentRouter()
    with pytest.raises(ValueError, match="Unknown compute intent"):
        router.route(task_def={}, intent="INVALID_INTENT")  # type: ignore


@pytest.mark.asyncio
async def test_latency_sla_exceeded_error_handling() -> None:
    """Test 2: Prove that raising a LatencySLAExceededError can be cleanly caught and handled."""

    async def dummy_async_execution() -> None:
        raise LatencySLAExceededError("Real-Time task took > 60s")

    with pytest.raises(LatencySLAExceededError) as exc_info:
        await dummy_async_execution()

    e = exc_info.value
    assert e.fault.error_code == "SLA-LATENCY-001"
    assert e.fault.severity == "RECOVERABLE"
    assert e.fault.recovery_action == "PROMPT_RETRY"
    assert "Real-Time task took > 60s" in str(e)
