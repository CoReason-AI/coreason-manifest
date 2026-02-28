from coreason_manifest.spec.core.workflow.nodes import LockConfig, SwarmNode


def test_swarm_concurrency_race_condition() -> None:
    from coreason_manifest.utils.validator import _validate_swarm_concurrency

    swarm = SwarmNode(
        id="swarm_1",
        worker_profile="p1",
        workload_variable="tasks",
        distribution_strategy="replicated",
        max_concurrency=5,
        reducer_function=None,  # Missing reducer
        lock_config=None,  # Missing locks
        output_variable="result",
        operational_policy=None,
    )

    errors = _validate_swarm_concurrency([swarm])
    race_errors = [e for e in errors if e.code == "ERR_TOPOLOGY_RACE_CONDITION"]

    assert len(race_errors) == 1  # noqa: S101
    assert "risking race conditions" in race_errors[0].message  # noqa: S101


def test_swarm_concurrency_safe_with_lock() -> None:
    from coreason_manifest.utils.validator import _validate_swarm_concurrency

    swarm = SwarmNode(
        id="swarm_1",
        worker_profile="p1",
        workload_variable="tasks",
        distribution_strategy="replicated",
        max_concurrency=5,
        reducer_function=None,
        lock_config=LockConfig(write_locks=["result"]),
        output_variable="result",
        operational_policy=None,
    )

    errors = _validate_swarm_concurrency([swarm])
    race_errors = [e for e in errors if e.code == "ERR_TOPOLOGY_RACE_CONDITION"]

    assert len(race_errors) == 0  # noqa: S101
