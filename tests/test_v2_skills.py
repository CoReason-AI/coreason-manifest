# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import AgentDefinition, AgentStep, ManifestV2, SkillDefinition
from coreason_manifest.spec.v2.skills import LoadStrategy, SkillDependency


def test_skill_definition_valid_eager() -> None:
    """Test creating a valid EAGER skill with inline instructions."""
    skill = SkillDefinition(
        id="basic-skill",
        name="Basic Skill",
        description="A basic skill.",
        load_strategy=LoadStrategy.EAGER,
        instructions="Do the thing.",
    )
    assert skill.id == "basic-skill"
    assert skill.load_strategy == LoadStrategy.EAGER
    assert skill.instructions == "Do the thing."


def test_skill_definition_valid_lazy() -> None:
    """Test creating a valid LAZY skill with trigger intent and external instructions."""
    skill = SkillDefinition(
        id="lazy-skill",
        name="Lazy Skill",
        description="A lazy skill.",
        load_strategy=LoadStrategy.LAZY,
        trigger_intent="User asks for lazy things.",
        instructions_uri="./skills/lazy.md",
        scripts={"run": "./scripts/run.py"},
        dependencies=[SkillDependency(ecosystem="python", package="requests", version_constraint=">=2.0.0")],
    )
    assert skill.load_strategy == LoadStrategy.LAZY
    assert skill.trigger_intent == "User asks for lazy things."
    assert skill.instructions_uri == "./skills/lazy.md"
    assert len(skill.scripts) == 1
    assert len(skill.dependencies) == 1
    assert skill.dependencies[0].package == "requests"


def test_skill_validation_lazy_requires_intent() -> None:
    """Test that LAZY loading requires trigger_intent."""
    with pytest.raises(ValidationError) as exc:
        SkillDefinition(
            id="invalid-lazy",
            name="Invalid Lazy",
            description="Missing intent.",
            load_strategy=LoadStrategy.LAZY,
            instructions="Do it.",
        )
    assert "Lazy loading requires a `trigger_intent`" in str(exc.value)


def test_skill_validation_instructions_xor() -> None:
    """Test XOR validation for instructions and instructions_uri."""
    # Case 1: Both present
    with pytest.raises(ValidationError) as exc:
        SkillDefinition(
            id="both-instr",
            name="Both",
            description="Both instructions.",
            load_strategy=LoadStrategy.EAGER,
            instructions="Inline",
            instructions_uri="./file.md",
        )
    assert "Cannot specify both" in str(exc.value)

    # Case 2: Neither present
    with pytest.raises(ValidationError) as exc:
        SkillDefinition(
            id="neither-instr",
            name="Neither",
            description="Neither instructions.",
            load_strategy=LoadStrategy.EAGER,
        )
    assert "Must specify either" in str(exc.value)


def test_agent_definition_with_skills() -> None:
    """Test that an Agent can be equipped with skills."""
    agent = AgentDefinition(
        id="agent-1",
        name="Skilled Agent",
        role="Worker",
        goal="Work",
        skills=["skill-1", "skill-2"],
    )
    assert agent.skills == ["skill-1", "skill-2"]


def test_manifest_v2_with_skills() -> None:
    """Test a full ManifestV2 containing skills and agents using them."""
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Skill Workflow"},
        "definitions": {
            "pdf-skill": {
                "type": "skill",
                "id": "pdf-skill",
                "name": "PDF Skill",
                "description": "Handles PDFs",
                "load_strategy": "lazy",
                "trigger_intent": "User mentions PDF",
                "instructions_uri": "./pdf.md",
            },
            "worker-agent": {
                "type": "agent",
                "id": "worker-agent",
                "name": "Worker",
                "role": "Clerk",
                "goal": "Process docs",
                "skills": ["pdf-skill"],
            },
        },
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "agent",
                    "id": "step-1",
                    "agent": "worker-agent",
                }
            },
        },
    }

    manifest = ManifestV2.model_validate(data)
    assert "pdf-skill" in manifest.definitions
    skill = manifest.definitions["pdf-skill"]
    assert isinstance(skill, SkillDefinition)
    assert skill.load_strategy == LoadStrategy.LAZY

    agent = manifest.definitions["worker-agent"]
    assert isinstance(agent, AgentDefinition)
    assert "pdf-skill" in agent.skills


def test_skill_edge_cases() -> None:
    """Test edge cases for SkillDefinition."""
    # Edge Case: Empty scripts and dependencies
    skill = SkillDefinition(
        id="empty-extras",
        name="Empty Extras",
        description="No scripts or deps",
        load_strategy=LoadStrategy.EAGER,
        instructions="Simple.",
        scripts={},
        dependencies=[],
    )
    assert skill.scripts == {}
    assert skill.dependencies == []

    # Edge Case: Weird dependency versions (should be allowed as string)
    skill_weird_dep = SkillDefinition(
        id="weird-dep",
        name="Weird Dep",
        description="Weird version",
        load_strategy=LoadStrategy.EAGER,
        instructions="Simple.",
        dependencies=[SkillDependency(ecosystem="python", package="pkg", version_constraint="<3.0.0,!=2.5.0")],
    )
    assert skill_weird_dep.dependencies[0].version_constraint == "<3.0.0,!=2.5.0"


def test_complex_manifest_scenario() -> None:
    """Test a complex scenario with mixed definitions."""
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Complex Workflow"},
        "definitions": {
            "skill-A": {
                "type": "skill",
                "id": "skill-A",
                "name": "Skill A",
                "description": "A",
                "load_strategy": "eager",
                "instructions": "A instructions",
            },
            "skill-B": {
                "type": "skill",
                "id": "skill-B",
                "name": "Skill B",
                "description": "B",
                "load_strategy": "user",
                "instructions": "B instructions",
            },
            "tool-1": {
                "type": "tool",
                "id": "tool-1",
                "name": "Tool 1",
                "uri": "http://mcp.local/tool",
                "risk_level": "safe",
            },
            "agent-X": {
                "type": "agent",
                "id": "agent-X",
                "name": "Agent X",
                "role": "X",
                "goal": "X",
                "skills": ["skill-A"],
                "tools": ["tool-1"],
            },
            "agent-Y": {
                "type": "agent",
                "id": "agent-Y",
                "name": "Agent Y",
                "role": "Y",
                "goal": "Y",
                "skills": ["skill-A", "skill-B"],
            },
        },
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {"type": "agent", "id": "step-1", "agent": "agent-X", "next": "step-2"},
                "step-2": {"type": "agent", "id": "step-2", "agent": "agent-Y"},
            },
        },
    }

    manifest = ManifestV2.model_validate(data)
    assert len(manifest.definitions) == 5
    assert isinstance(manifest.definitions["skill-A"], SkillDefinition)

    # Check if ToolDefinition is properly instantiated
    from coreason_manifest.spec.v2.definitions import ToolDefinition

    assert isinstance(manifest.definitions["tool-1"], ToolDefinition)


def test_skill_edge_cases_extended() -> None:
    """Test extended edge cases for SkillDefinition."""
    # 1. Extremely long strings
    long_string = "a" * 10000
    skill_long = SkillDefinition(
        id="long-skill",
        name="Long Skill",
        description=long_string,
        load_strategy=LoadStrategy.EAGER,
        instructions=long_string,
        trigger_intent=long_string,
    )
    assert len(skill_long.description) == 10000
    assert skill_long.instructions is not None
    assert len(skill_long.instructions) == 10000

    # 2. Extra forbidden fields (should raise ValidationError)
    with pytest.raises(ValidationError) as exc:
        SkillDefinition(
            id="extra-fields",
            name="Extra",
            description="Extra fields",
            load_strategy=LoadStrategy.EAGER,
            instructions="Simple.",
            extra_field="forbidden",  # type: ignore[call-arg]
        )
    assert "Extra inputs are not permitted" in str(exc.value)

    # 3. Scripts with empty values (valid schema, runtime concern)
    skill_empty_script = SkillDefinition(
        id="empty-script",
        name="Empty Script",
        description="Empty script path",
        load_strategy=LoadStrategy.EAGER,
        instructions="Simple.",
        scripts={"run": ""},
    )
    assert skill_empty_script.scripts["run"] == ""

    # 4. Dependencies with empty fields
    # Package is required, but empty string is technically a string (unless min_length is set, which isn't)
    # Let's check if we can pass empty strings
    skill_empty_dep = SkillDefinition(
        id="empty-dep",
        name="Empty Dep",
        description="Empty dep package",
        load_strategy=LoadStrategy.EAGER,
        instructions="Simple.",
        dependencies=[SkillDependency(ecosystem="python", package="")],
    )
    assert skill_empty_dep.dependencies[0].package == ""


def test_complex_scenarios_extended() -> None:
    """Test extended complex scenarios for SkillDefinition."""
    # 1. Mixed Load Strategies in one Manifest
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Mixed Strategies"},
        "definitions": {
            "skill-eager": {
                "type": "skill",
                "id": "skill-eager",
                "name": "Eager",
                "description": "Eager",
                "load_strategy": "eager",
                "instructions": "Eager instructions",
            },
            "skill-lazy": {
                "type": "skill",
                "id": "skill-lazy",
                "name": "Lazy",
                "description": "Lazy",
                "load_strategy": "lazy",
                "trigger_intent": "Lazy trigger",
                "instructions_uri": "./lazy.md",
            },
            "skill-user": {
                "type": "skill",
                "id": "skill-user",
                "name": "User",
                "description": "User",
                "load_strategy": "user",
                "instructions": "User instructions",
            },
            "mega-agent": {
                "type": "agent",
                "id": "mega-agent",
                "name": "Mega Agent",
                "role": "Mega",
                "goal": "All",
                "skills": ["skill-eager", "skill-lazy", "skill-user"],
            },
        },
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {"type": "agent", "id": "step-1", "agent": "mega-agent"},
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    agent = manifest.definitions["mega-agent"]
    assert isinstance(agent, AgentDefinition)
    assert len(agent.skills) == 3

    # 2. Shared Dependencies across Skills
    skill_a = SkillDefinition(
        id="skill-a",
        name="A",
        description="A",
        load_strategy=LoadStrategy.EAGER,
        instructions="A",
        dependencies=[SkillDependency(ecosystem="python", package="pandas", version_constraint=">=2.0")],
    )
    skill_b = SkillDefinition(
        id="skill-b",
        name="B",
        description="B",
        load_strategy=LoadStrategy.EAGER,
        instructions="B",
        dependencies=[SkillDependency(ecosystem="python", package="pandas", version_constraint=">=2.1")],
    )
    # This is valid at schema level, runtime must resolve conflict
    assert skill_a.dependencies[0].package == skill_b.dependencies[0].package

    # 3. Workflow Data Passing (Simulated)
    # This just ensures ManifestV2 structure supports inputs/outputs in steps even with skills involved
    workflow_data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Data Flow"},
        "definitions": {
            "skill-extract": {
                "type": "skill",
                "id": "skill-extract",
                "name": "Extract",
                "description": "Extracts data",
                "load_strategy": "eager",
                "instructions": "Extract data.",
            },
            "extractor-agent": {
                "type": "agent",
                "id": "extractor-agent",
                "name": "Extractor",
                "role": "Extractor",
                "goal": "Extract",
                "skills": ["skill-extract"],
            },
            "processor-agent": {
                "type": "agent",
                "id": "processor-agent",
                "name": "Processor",
                "role": "Processor",
                "goal": "Process",
            },
        },
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {"type": "agent", "id": "step-1", "agent": "extractor-agent", "next": "step-2"},
                "step-2": {
                    "type": "agent",
                    "id": "step-2",
                    "agent": "processor-agent",
                    "inputs": {"data": "{{ step-1.output }}"},
                },
            },
        },
    }
    manifest_flow = ManifestV2.model_validate(workflow_data)
    step2 = manifest_flow.workflow.steps["step-2"]
    assert step2.inputs["data"] == "{{ step-1.output }}"


def test_sota_agent_fields() -> None:
    """Test SOTA enhancements for AgentDefinition and AgentStep."""
    # 1. AgentDefinition with context_strategy
    agent = AgentDefinition(
        id="sota-agent",
        name="SOTA Agent",
        role="SOTA",
        goal="SOTA",
        skills=["skill-1"],
        context_strategy="compressed",
    )
    assert agent.context_strategy == "compressed"
    assert agent.skills == ["skill-1"]

    # 2. AgentStep with temporary_skills
    step = AgentStep(
        id="step-1",
        agent="sota-agent",
        temporary_skills=["temp-skill"],
    )
    assert step.temporary_skills == ["temp-skill"]
