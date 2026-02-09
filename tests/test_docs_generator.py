# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import ClassVar

from coreason_manifest import (
    AgentDefinition,
    AgentStep,
    EvaluationProfile,
    InterfaceDefinition,
    Manifest,
    ManifestMetadata,
    ModelProfile,
    PricingUnit,
    RateCard,
    ResourceConstraints,
    SuccessCriterion,
    ToolDefinition,
    Workflow,
    render_agent_card,
)


def test_render_full_agent() -> None:
    # 1. Create components
    resources = ModelProfile(
        provider="openai",
        model_id="gpt-4",
        pricing=RateCard(
            unit=PricingUnit.TOKEN_1M,
            input_cost=10.0,
            output_cost=30.0,
            currency="USD",
        ),
        constraints=ResourceConstraints(
            context_window_size=128000,
        ),
    )

    evaluation = EvaluationProfile(
        expected_latency_ms=2000,
        grading_rubric=[
            SuccessCriterion(
                name="accuracy",
                description="Must be accurate",
                threshold=0.9,
            )
        ],
    )

    agent_def = AgentDefinition(
        id="researcher",
        name="Researcher",
        role="Research Assistant",
        goal="Find information",
        backstory="You are a diligent researcher.\nYou cite sources.",
        resources=resources,
        evaluation=evaluation,
    )

    metadata = ManifestMetadata(
        name="Researcher",
        version="1.0.0",  # Extra field
    )

    interface = InterfaceDefinition(
        inputs={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "depth": {"type": "integer", "description": "Search depth"},
            },
            "required": ["query"],
        },
        outputs={
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Result summary"},
            },
        },
    )

    manifest = Manifest(
        kind="Agent",
        metadata=metadata,
        interface=interface,
        definitions={"Researcher": agent_def},
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="Researcher")}),
    )

    card = render_agent_card(manifest)

    # Assertions
    assert "# Researcher (v1.0.0)" in card
    assert "**Role:** Research Assistant" in card
    assert "> You are a diligent researcher." in card

    assert "## 💰 Resource & Cost Profile" in card
    assert "**Model:** openai/gpt-4" in card
    assert "**Pricing:** $10.0 / 1M Input | $30.0 / 1M Output" in card
    assert "**Context Window:** 128000 tokens" in card

    assert "## 🔌 API Interface" in card
    assert "| `query` | `string` | Yes | Search query |" in card
    assert "| `depth` | `integer` | No | Search depth |" in card
    assert "| `summary` | `string` | No | Result summary |" in card

    assert "## 🧪 Evaluation Standards" in card
    assert "**accuracy:** Must be accurate (Threshold: 0.9)" in card
    assert "**SLA:** 2000ms latency" in card


def test_render_minimal_agent() -> None:
    agent_def = AgentDefinition(
        id="minimal",
        name="Minimal",
        role="Minion",
        goal="Do little",
    )

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Minimal"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="Minimal")}),
        definitions={"Minimal": agent_def},
    )

    card = render_agent_card(manifest)

    assert "# Minimal (v0.0.0)" in card
    assert "**Role:** Minion" in card
    assert "## 💰 Resource & Cost Profile" not in card
    assert "## 🧪 Evaluation Standards" not in card
    assert "## 🔌 API Interface" in card
    assert "_No fields defined._" in card


def test_schema_parsing() -> None:
    interface = InterfaceDefinition(
        inputs={
            "type": "object",
            "properties": {
                "field_a": {"type": "string"},
                "field_b": {"type": "number"},
            },
            "required": ["field_b"],
        }
    )

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="SchemaTest"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="SchemaTest")}),
        interface=interface,
        definitions={"SchemaTest": AgentDefinition(id="SchemaTest", name="SchemaTest", role="Tester", goal="Test")},
    )

    card = render_agent_card(manifest)

    assert "| `field_a` | `string` | No | - |" in card
    assert "| `field_b` | `number` | Yes | - |" in card


class MockGovernance:
    risk_level: ClassVar[str] = "standard"
    policies: ClassVar[list[str]] = ["No rude language"]


class MockManifest:
    def __init__(self) -> None:
        self.metadata = ManifestMetadata(name="GovBot")
        self.definitions = {}  # type: ignore
        self.interface = InterfaceDefinition()
        self.governance = MockGovernance()


def test_governance_render() -> None:
    # We need to cast to ManifestV2 for typing but at runtime it works
    manifest = MockManifest()

    card = render_agent_card(manifest)  # type: ignore

    assert "## 🛡️ Governance & Safety" in card
    assert "**Risk Level:** standard" in card
    assert "- No rude language" in card


def test_render_fallback_lookup() -> None:
    """Test finding AgentDefinition when name doesn't match."""
    agent_def = AgentDefinition(
        id="hidden",
        name="HiddenAgent",
        role="Ninja",
        goal="Hide",
    )

    # Metadata name "PublicFace" does not match definition key "HiddenAgent"
    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="PublicFace"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="HiddenAgent")}),
        definitions={"HiddenAgent": agent_def},
    )

    card = render_agent_card(manifest)

    assert "# PublicFace" in card
    assert "**Role:** Ninja" in card


def test_render_metadata_variants() -> None:
    """Test version conversion, created date, and description fallback."""
    # We use a Mock object that passes isinstance(x, AgentDefinition) check by manual patching
    # or by simply injecting it if render_agent_card uses duck typing.
    # However, render_agent_card uses isinstance.
    # To bypass Pydantic extra fields restriction, we can't easily subclass.
    # But we can use unittest.mock to simulate the object structure.

    # We create a mock that behaves like an AgentDefinition but has a description
    # Since render_agent_card checks isinstance(x, AgentDefinition), we need a way to trick it.
    # OR we assume the intent was duck typing and fix the implementation?
    # The implementation explicitly checks isinstance.
    # Given we can't change implementation now (freeze), we must create a valid AgentDefinition
    # OR acknowledge that the 'description' fallback branch is dead code for AgentDefinition
    # unless it's a subclass.

    # Let's try to create a subclass that allows extra fields.
    from pydantic import ConfigDict

    class ExtendedAgentDefinition(AgentDefinition):
        model_config = ConfigDict(extra="allow")

    agent_def = ExtendedAgentDefinition(
        id="describer",
        name="Describer",
        role="Scribe",
        goal="Write",
        description="I describe things.",  # This is now allowed
    )

    metadata = ManifestMetadata(
        name="Describer",
        version=2.5,  # Float version to trigger str() conversion
        created="2025-01-01",  # Extra field
    )

    manifest = Manifest(
        kind="Agent",
        metadata=metadata,
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="Describer")}),
        definitions={"Describer": agent_def},
    )

    card = render_agent_card(manifest)

    assert "# Describer (v2.5)" in card
    assert "**Created:** 2025-01-01" in card
    # Should not be quoted
    assert "\nI describe things." in card
    assert "> I describe things." not in card


def test_render_pricing_units() -> None:
    """Test different pricing units."""
    resources = ModelProfile(
        provider="test",
        model_id="cheap",
        pricing=RateCard(
            unit=PricingUnit.TOKEN_1K,  # Trigger "1k" logic
            input_cost=0.01,
            output_cost=0.02,
            currency="USD",
        ),
        constraints=ResourceConstraints(context_window_size=1000),
    )

    agent_def = AgentDefinition(
        id="cheap_agent",
        name="Cheap",
        role="Saver",
        goal="Save money",
        resources=resources,
    )

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Cheap"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="Cheap")}),
        definitions={"Cheap": agent_def},
    )

    card = render_agent_card(manifest)

    assert "$0.01 / 1k Input" in card
    assert "$0.02 / 1k Output" in card


def test_render_pricing_unit_other() -> None:
    """Test pricing unit that is neither TOKEN_1M nor TOKEN_1K."""
    resources = ModelProfile(
        provider="test",
        model_id="per_request",
        pricing=RateCard(
            unit=PricingUnit.REQUEST,  # Trigger fallback logic
            input_cost=0.05,
            output_cost=0.0,
            currency="USD",
        ),
        constraints=ResourceConstraints(context_window_size=1000),
    )

    agent_def = AgentDefinition(
        id="request_agent",
        name="RequestBased",
        role="Worker",
        goal="Work",
        resources=resources,
    )

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="RequestBased"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="RequestBased")}),
        definitions={"RequestBased": agent_def},
    )

    card = render_agent_card(manifest)

    # Should contain "REQUEST" directly
    assert "$0.05 / REQUEST Input" in card


def test_edge_case_empty_schema() -> None:
    """Test that empty input/output schemas render without errors."""
    interface = InterfaceDefinition(
        inputs={},  # Empty dict
        outputs={"type": "object"},  # Valid type but no properties
    )

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="EmptySchema"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="EmptySchema")}),
        definitions={"EmptySchema": AgentDefinition(id="es", name="EmptySchema", role="None", goal="None")},
        interface=interface,
    )

    card = render_agent_card(manifest)

    assert "_No fields defined._" in card
    # Should appear twice (once for inputs, once for outputs)
    assert card.count("_No fields defined._") == 2


def test_edge_case_markdown_injection() -> None:
    """Test robustness against Markdown characters in fields."""
    agent_def = AgentDefinition(
        id="injector",
        name="**Bold**|Table",
        role="Injector",
        goal="Inject",
        backstory="# I am header\n* list",
    )

    interface = InterfaceDefinition(
        inputs={
            "properties": {
                "field|pipe": {"type": "string", "description": "**BoldDesc** | Pipe"},
            }
        }
    )

    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="Injector"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="Injector")}),
        definitions={"Injector": agent_def},
        interface=interface,
    )

    card = render_agent_card(manifest)

    # Verify things are rendered (even if markup is broken, it shouldn't crash)
    assert "> # I am header" in card
    assert "`field|pipe`" in card
    assert "**BoldDesc** | Pipe" in card


def test_complex_multi_agent_manifest() -> None:
    """Test manifest with multiple definitions (Tools, multiple Agents)."""
    agent1 = AgentDefinition(id="a1", name="AgentOne", role="Role1", goal="Goal1")
    agent2 = AgentDefinition(id="a2", name="AgentTwo", role="Role2", goal="Goal2")
    tool = ToolDefinition(id="t1", name="ToolOne", uri="http://example.com", risk_level="safe")

    # Name matches AgentTwo
    manifest = Manifest(
        kind="Agent",
        metadata=ManifestMetadata(name="AgentTwo"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="AgentTwo")}),
        definitions={
            "AgentOne": agent1,
            "ToolOne": tool,
            "AgentTwo": agent2,
        },
    )

    card = render_agent_card(manifest)

    # Should select AgentTwo based on name match
    assert "# AgentTwo" in card
    assert "**Role:** Role2" in card
    assert "Role1" not in card
