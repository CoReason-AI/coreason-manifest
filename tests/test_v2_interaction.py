import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GenerativeNode,
    GraphTopology,
    InteractionConfig,
    InterventionTrigger,
    RecipeNode,
    TransparencyLevel,
    TaskSequence,
)


def test_interaction_primitives_exist():
    """Verify that interaction primitives are importable and defined correctly."""
    assert TransparencyLevel.OPAQUE == "opaque"
    assert TransparencyLevel.OBSERVABLE == "observable"
    assert TransparencyLevel.INTERACTIVE == "interactive"

    assert InterventionTrigger.ON_START == "on_start"
    assert InterventionTrigger.ON_PLAN_GENERATION == "on_plan_generation"
    assert InterventionTrigger.ON_FAILURE == "on_failure"
    assert InterventionTrigger.ON_COMPLETION == "on_completion"


def test_interaction_config_defaults():
    """Verify default values for InteractionConfig."""
    config = InteractionConfig()
    assert config.transparency == TransparencyLevel.OPAQUE
    assert config.triggers == []
    assert config.editable_fields == []
    assert config.guidance_hint is None


def test_agent_node_interaction_support():
    """Verify AgentNode supports interaction configuration."""
    interaction = InteractionConfig(
        transparency=TransparencyLevel.INTERACTIVE,
        triggers=[InterventionTrigger.ON_START, InterventionTrigger.ON_FAILURE],
        editable_fields=["inputs", "system_prompt_override"],
        guidance_hint="Review the inputs carefully."
    )

    node = AgentNode(
        id="agent_1",
        agent_ref="agent/v1/summarizer",
        interaction=interaction
    )

    assert node.interaction is not None
    assert node.interaction.transparency == TransparencyLevel.INTERACTIVE
    assert InterventionTrigger.ON_START in node.interaction.triggers
    assert "inputs" in node.interaction.editable_fields
    assert node.interaction.guidance_hint == "Review the inputs carefully."


def test_generative_node_interaction_support():
    """Verify GenerativeNode supports interaction configuration."""
    interaction = InteractionConfig(
        transparency=TransparencyLevel.OBSERVABLE,
        triggers=[InterventionTrigger.ON_PLAN_GENERATION],
        editable_fields=["goal", "solver.n_samples"],
        guidance_hint="Check if the plan covers all edge cases."
    )

    node = GenerativeNode(
        id="gen_1",
        goal="Generate a report",
        output_schema={"type": "object"},
        interaction=interaction
    )

    assert node.interaction is not None
    assert node.interaction.transparency == TransparencyLevel.OBSERVABLE
    assert InterventionTrigger.ON_PLAN_GENERATION in node.interaction.triggers
    assert "solver.n_samples" in node.interaction.editable_fields


def test_serialization():
    """Verify that interaction config serializes correctly."""
    interaction = InteractionConfig(
        transparency=TransparencyLevel.INTERACTIVE,
        triggers=[InterventionTrigger.ON_COMPLETION]
    )

    node = AgentNode(
        id="agent_1",
        agent_ref="agent/v1/test",
        interaction=interaction
    )

    dumped = node.dump()
    assert "interaction" in dumped
    assert dumped["interaction"]["transparency"] == "interactive"
    assert dumped["interaction"]["triggers"] == ["on_completion"]


def test_validation_rejects_invalid_enums():
    """Verify validation fails for invalid enum values."""
    with pytest.raises(ValidationError) as excinfo:
        InteractionConfig(transparency="invalid_level") # type: ignore
    assert "Input should be 'opaque', 'observable' or 'interactive'" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        InteractionConfig(triggers=["invalid_trigger"]) # type: ignore
    assert "Input should be 'on_start', 'on_plan_generation', 'on_failure' or 'on_completion'" in str(excinfo.value)

def test_inheritance_check():
    """Verify that interaction field is inherited from RecipeNode."""
    # This is implicitly tested by AgentNode and GenerativeNode usage,
    # but we can explicitly check isinstance if we really want, or just rely on the above tests.
    node = AgentNode(id="a1", agent_ref="ref")
    assert isinstance(node, RecipeNode)
    assert hasattr(node, "interaction")
    assert node.interaction is None

# --- Edge Case Tests ---

def test_edge_case_empty_values():
    """Verify that empty lists and strings are handled correctly."""
    interaction = InteractionConfig(
        triggers=[],
        editable_fields=[],
        guidance_hint=""
    )
    assert interaction.triggers == []
    assert interaction.editable_fields == []
    assert interaction.guidance_hint == ""

def test_edge_case_nested_editable_fields():
    """Verify that nested field paths are accepted (they are just strings)."""
    interaction = InteractionConfig(
        editable_fields=["solver.n_samples", "metadata.version", "deeply.nested.field"]
    )
    assert "deeply.nested.field" in interaction.editable_fields

def test_edge_case_all_triggers():
    """Verify that all triggers can be active simultaneously."""
    triggers = [
        InterventionTrigger.ON_START,
        InterventionTrigger.ON_PLAN_GENERATION,
        InterventionTrigger.ON_FAILURE,
        InterventionTrigger.ON_COMPLETION
    ]
    interaction = InteractionConfig(triggers=triggers)
    assert len(interaction.triggers) == 4
    assert set(interaction.triggers) == set(triggers)

def test_edge_case_duplicate_triggers():
    """Verify behavior with duplicate triggers (should be allowed by list, though redundant)."""
    # Pydantic doesn't deduplicate lists by default unless using set, but our schema says list.
    triggers = [InterventionTrigger.ON_START, InterventionTrigger.ON_START]
    interaction = InteractionConfig(triggers=triggers)
    assert len(interaction.triggers) == 2
    assert interaction.triggers[0] == InterventionTrigger.ON_START

# --- Complex Case Tests ---

def test_complex_graph_mixed_interactions():
    """Verify a topology with nodes having different interaction configurations."""

    # Node 1: Interactive Agent
    agent_node = AgentNode(
        id="agent_1",
        agent_ref="ref_1",
        interaction=InteractionConfig(
            transparency=TransparencyLevel.INTERACTIVE,
            triggers=[InterventionTrigger.ON_FAILURE]
        )
    )

    # Node 2: Observable Generative Node
    gen_node = GenerativeNode(
        id="gen_1",
        goal="Solve X",
        output_schema={},
        interaction=InteractionConfig(
            transparency=TransparencyLevel.OBSERVABLE,
            triggers=[InterventionTrigger.ON_PLAN_GENERATION]
        )
    )

    # Node 3: Opaque Agent (Default)
    opaque_node = AgentNode(
        id="agent_2",
        agent_ref="ref_2"
        # interaction is None
    )

    # Create Topology
    topology = TaskSequence(steps=[agent_node, gen_node, opaque_node]).to_graph()

    assert len(topology.nodes) == 3

    # Verify Node 1
    n1 = next(n for n in topology.nodes if n.id == "agent_1")
    assert n1.interaction.transparency == TransparencyLevel.INTERACTIVE

    # Verify Node 2
    n2 = next(n for n in topology.nodes if n.id == "gen_1")
    assert n2.interaction.transparency == TransparencyLevel.OBSERVABLE

    # Verify Node 3
    n3 = next(n for n in topology.nodes if n.id == "agent_2")
    assert n3.interaction is None

def test_complex_interaction_modification_immutability():
    """Verify that InteractionConfig is frozen (immutable)."""
    interaction = InteractionConfig(transparency=TransparencyLevel.OPAQUE)
    with pytest.raises(ValidationError):
        interaction.transparency = TransparencyLevel.INTERACTIVE # type: ignore
