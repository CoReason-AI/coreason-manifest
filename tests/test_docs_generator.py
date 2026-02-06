# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest import (
    AgentDefinition,
    AgentStep,
    EvaluationProfile,
    InterfaceDefinition,
    ManifestMetadata,
    ManifestV2,
    ModelProfile,
    PricingUnit,
    RateCard,
    ResourceConstraints,
    SuccessCriterion,
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

    manifest = ManifestV2(
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

    manifest = ManifestV2(
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

    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="SchemaTest"),
        workflow=Workflow(start="main", steps={"main": AgentStep(id="main", agent="SchemaTest")}),
        interface=interface,
    )

    card = render_agent_card(manifest)

    assert "| `field_a` | `string` | No | - |" in card
    assert "| `field_b` | `number` | Yes | - |" in card


class MockGovernance:
    risk_level = "standard"
    policies = ["No rude language"]


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
