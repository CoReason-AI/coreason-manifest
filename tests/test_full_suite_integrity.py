from coreason_manifest.builder import NewLinearFlow, NewGraphFlow
from coreason_manifest.spec.core.nodes import Placeholder
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.utils.visualizer import to_mermaid
from coreason_manifest.utils.langchain_adapter import flow_to_langchain_config

def test_full_suite_integrity() -> None:
    """
    Verifies the end-to-end functionality of the new Core Kernel without V2 files.
    """
    # 1. Build a simple LinearFlow using the Builder
    builder = NewLinearFlow("IntegrityCheck", version="1.0", description="Verifying Core Integrity")

    node1 = Placeholder(
        id="step-1",
        metadata={},
        supervision=None,
        required_capabilities=["logging"],
        type="placeholder"
    )
    node2 = Placeholder(
        id="step-2",
        metadata={},
        supervision=None,
        required_capabilities=["alerting"],
        type="placeholder"
    )

    builder.add_step(node1)
    builder.add_step(node2)

    flow = builder.build()

    # 2. Validate it (should be valid)
    errors = validate_flow(flow)
    assert not errors, f"Validation failed with errors: {errors}"
    assert flow.metadata.name == "IntegrityCheck"
    assert len(flow.sequence) == 2

    # 3. Visualize it (should return Mermaid string)
    mermaid_diagram = to_mermaid(flow)
    assert "graph TD" in mermaid_diagram
    assert "step_1 --> step_2" in mermaid_diagram
    assert "step_1" in mermaid_diagram
    assert "step_2" in mermaid_diagram

    # 4. Adapt it (should return LangChain config)
    lc_config = flow_to_langchain_config(flow)
    assert lc_config["type"] == "chain"
    assert lc_config["steps"] == ["step-1", "step-2"]
