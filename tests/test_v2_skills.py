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

from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2, SkillDefinition
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
