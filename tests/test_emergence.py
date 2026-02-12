from coreason_manifest.spec.core.engines import RedTeamingReasoning
from coreason_manifest.spec.core.nodes import EmergenceInspectorNode


def test_red_teaming_emergence_boosting() -> None:
    # Test that 'emergence_boosting' is a valid attack strategy
    rt = RedTeamingReasoning(
        model="gpt-4",
        attacker_model="gpt-4-turbo",
        attack_strategy="emergence_boosting",
        success_criteria="Detect latent capabilities",
    )
    assert rt.attack_strategy == "emergence_boosting"


def test_emergence_inspector_instantiation() -> None:
    # Test EmergenceInspectorNode defaults
    inspector = EmergenceInspectorNode(
        id="inspector-001",
        metadata={},
        supervision=None,
        target_variable="agent_response",
        criteria="Check for hidden goals",
        output_variable="is_safe",
        judge_model="gpt-4",
    )

    assert inspector.type == "emergence_inspector"
    assert inspector.detect_sycophancy is True
    assert inspector.detect_power_seeking is True
    assert inspector.detect_deception is True
    assert inspector.mode == "semantic"
    assert inspector.judge_model == "gpt-4"

    # Test custom configuration
    inspector_custom = EmergenceInspectorNode(
        id="inspector-002",
        metadata={},
        supervision=None,
        target_variable="response",
        criteria="Check for deception only",
        output_variable="is_deceptive",
        judge_model="claude-3-opus",
        detect_sycophancy=False,
        detect_power_seeking=False,
    )
    assert inspector_custom.detect_sycophancy is False
    assert inspector_custom.detect_power_seeking is False
    assert inspector_custom.detect_deception is True
