from coreason_manifest.builder import NewLinearFlow
from coreason_manifest.spec.core.workflow.evals import EvalsManifest, FuzzingTarget
from coreason_manifest.spec.core.workflow.nodes import PlannerNode
from coreason_manifest.utils.mock import MockFactory


def test_epic12_fuzzing_targets() -> None:
    builder = NewLinearFlow("fuzz_flow", "1.0.0")

    planner = PlannerNode(
        id="planner1",
        type="planner",
        metadata={},
        goal="Produce output",
        output_schema={
            "type": "object",
            "properties": {"user_input": {"type": "string"}, "safe_input": {"type": "string"}},
        },
    )

    builder.add_step(planner)
    flow = builder.build()

    evals = EvalsManifest(test_cases=[], fuzzing_targets=[FuzzingTarget(variables=["user_input"])])

    mock_factory = MockFactory(seed=42)
    trace = mock_factory.simulate_trace(flow, evals=evals)

    assert len(trace) == 1  # noqa: S101
    outputs = trace[0].outputs

    assert "user_input" in outputs  # noqa: S101
    assert "safe_input" in outputs  # noqa: S101

    # user_input should be fuzzed
    fuzzed_val = outputs["user_input"]
    assert fuzzed_val in [  # noqa: S101
        "A" * 100000,
        -999999999,
        "'; DROP TABLE users; --",
        "<script>alert(1)</script>",
        "\x00" * 100,
    ]

    # safe_input should not be fuzzed
    assert outputs["safe_input"] == "lorem ipsum"  # noqa: S101
