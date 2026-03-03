from coreason_manifest.core.workflow.evals import (
    AdversaryProfile,
    ChaosConfig,
    EvalsManifest,
    SimulationScenario,
    ValidationLogic,
)


def test_adversary_profile_valid() -> None:
    """Test creating an AdversaryProfile with new fields."""
    profile = AdversaryProfile(
        goal="Extract PII",
        attack_strategy="Prompt Injection",
        strategy_model="gpt-4",
        attack_model="gpt-3.5-turbo",
    )
    assert profile.goal == "Extract PII"
    assert profile.attack_strategy == "Prompt Injection"
    assert profile.strategy_model == "gpt-4"
    assert profile.attack_model == "gpt-3.5-turbo"


def test_simulation_scenario_valid() -> None:
    """Test valid SimulationScenario creation with full topology and configurations."""
    chaos = ChaosConfig(latency_ms=100, error_rate=0.1, token_throttle=True)
    adversary = AdversaryProfile(goal="Bypass filter", attack_strategy="Obfuscation", strategy_model="test-model")
    scenario = SimulationScenario(
        mock_inputs={"user_message": "Hello"},
        expected_traversal_path=["input_node", "processing_node", "output_node"],
        assertions={"output": {"type": "string"}},
        validation_logic=ValidationLogic.LLM_JUDGE,
        chaos_config=chaos,
        adversary=adversary,
    )

    assert scenario.mock_inputs["user_message"] == "Hello"
    assert scenario.expected_traversal_path == ["input_node", "processing_node", "output_node"]
    assert scenario.assertions["output"]["type"] == "string"
    assert scenario.validation_logic == ValidationLogic.LLM_JUDGE
    assert scenario.chaos_config == chaos
    assert scenario.adversary == adversary


def test_simulation_scenario_defaults() -> None:
    """Test SimulationScenario default values."""
    scenario = SimulationScenario()
    assert scenario.mock_inputs == {}
    assert scenario.expected_traversal_path == []
    assert scenario.assertions == {}
    assert scenario.validation_logic == ValidationLogic.EXACT_MATCH
    assert scenario.chaos_config is None
    assert scenario.adversary is None


def test_evals_manifest_valid() -> None:
    """Test EvalsManifest contains SimulationScenario."""
    scenario = SimulationScenario(
        expected_traversal_path=["start", "end"],
        validation_logic=ValidationLogic.JSON_SCHEMA_INVARIANT,
    )
    manifest = EvalsManifest(test_cases=[scenario], fuzzing_targets=[])
    assert len(manifest.test_cases) == 1
    assert manifest.test_cases[0] == scenario
    assert manifest.test_cases[0].validation_logic == ValidationLogic.JSON_SCHEMA_INVARIANT


def test_validation_logic_enum() -> None:
    """Test the ValidationLogic enum values."""
    assert ValidationLogic.EXACT_MATCH.value == "exact_match"
    assert ValidationLogic.FUZZY.value == "fuzzy"
    assert ValidationLogic.LLM_JUDGE.value == "llm_judge"
    assert ValidationLogic.SYMBOLIC_EXECUTION.value == "symbolic_execution"
    assert ValidationLogic.VLM_RUBRIC.value == "vlm_rubric"
    assert ValidationLogic.JSON_SCHEMA_INVARIANT.value == "json_schema_invariant"
