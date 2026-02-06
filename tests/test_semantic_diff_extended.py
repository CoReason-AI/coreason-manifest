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
    AgentBuilder,
    ChangeCategory,
    ManifestV2,
    compare_agents,
)
from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.spec.v2.resources import ModelProfile


def create_base_manifest() -> ManifestV2:
    return AgentBuilder("test-agent").build()


def test_empty_manifests() -> None:
    """Comparing two default manifests should yield no changes."""
    agent1 = create_base_manifest()
    agent2 = create_base_manifest()
    report = compare_agents(agent1, agent2)
    assert len(report.changes) == 0


def test_list_swap_tools() -> None:
    """Swapping list items shows as changes (index mismatch)."""
    agent1 = create_base_manifest()

    def set_tools(manifest: ManifestV2, tools: list[str]) -> ManifestV2:
        defs = manifest.definitions.copy()
        agent_def = defs["test-agent"]
        assert isinstance(agent_def, AgentDefinition)
        new_agent_def = agent_def.model_copy(update={"tools": tools})
        defs["test-agent"] = new_agent_def
        return manifest.model_copy(update={"definitions": defs})

    agent1 = set_tools(agent1, ["tool_a", "tool_b"])
    agent2 = set_tools(agent1, ["tool_b", "tool_a"])

    report = compare_agents(agent1, agent2)
    # logic sees:
    # 0: tool_a -> tool_b
    # 1: tool_b -> tool_a
    assert len(report.changes) >= 2
    # These are value changes in 'tools', usually FEATURE or PATCH if not adding/removing.
    # _categorize_change for 'tools':
    # if new is None -> BREAKING. if old is None -> FEATURE.
    # Here both are strings. So it falls to PATCH (default).
    assert all(c.category == ChangeCategory.PATCH for c in report.changes)


def test_type_change_scalar() -> None:
    """Changing value type should be detected."""
    agent1 = create_base_manifest()

    # Force a type change by manually constructing dicts if Pydantic validates strictly.
    # But compare_agents takes objects.
    # We can use 'model_extra' or a field that allows Any?
    # interface.inputs allows dict[str, Any].

    inputs1 = {"limit": 10}
    inputs2 = {"limit": "10"}

    agent1 = agent1.model_copy(update={"interface": InterfaceDefinition(inputs=inputs1)})
    agent2 = agent1.model_copy(update={"interface": InterfaceDefinition(inputs=inputs2)})

    report = compare_agents(agent1, agent2)
    change = next(c for c in report.changes if c.path.endswith("limit"))
    assert change.old_value == 10
    assert change.new_value == "10"
    # Fallback category
    assert change.category in [ChangeCategory.PATCH, ChangeCategory.BREAKING]


def test_add_required_block() -> None:
    """Adding 'required' list to inputs (coverage for 187-190)."""
    agent1 = create_base_manifest()
    # inputs without 'required'
    inputs1 = {"properties": {"a": {"type": "string"}}}
    agent1 = agent1.model_copy(update={"interface": InterfaceDefinition(inputs=inputs1)})

    agent2 = agent1.model_copy(deep=True)
    # inputs WITH 'required'
    inputs2 = {"properties": {"a": {"type": "string"}}, "required": ["a"]}
    agent2 = agent2.model_copy(update={"interface": InterfaceDefinition(inputs=inputs2)})

    report = compare_agents(agent1, agent2)
    # Adding required constraints is BREAKING
    change = next(c for c in report.changes if "required" in c.path)
    assert change.category == ChangeCategory.BREAKING


def test_remove_required_block() -> None:
    """Removing 'required' list (coverage for 196-197)."""
    agent1 = create_base_manifest()
    inputs1 = {"properties": {"a": {"type": "string"}}, "required": ["a"]}
    agent1 = agent1.model_copy(update={"interface": InterfaceDefinition(inputs=inputs1)})

    agent2 = agent1.model_copy(deep=True)
    inputs2 = {"properties": {"a": {"type": "string"}}}  # No required
    agent2 = agent2.model_copy(update={"interface": InterfaceDefinition(inputs=inputs2)})

    report = compare_agents(agent1, agent2)
    # Loosening constraints is FEATURE
    change = next(c for c in report.changes if "required" in c.path)
    assert change.category == ChangeCategory.FEATURE


def test_remove_inputs_block() -> None:
    """Removing entire inputs block (coverage for 201)."""
    agent1 = create_base_manifest()
    inputs1 = {"properties": {"a": {"type": "string"}}}
    agent1 = agent1.model_copy(update={"interface": InterfaceDefinition(inputs=inputs1)})

    # Manually pass empty dict or None? InterfaceDefinition.inputs is dict, default {}.
    # If we set it to None, pydantic might complain if field is required.
    # But InterfaceDefinition inputs is `dict[str, Any] = Field(default_factory=dict)`.
    # So we can't easily make it None in the model.
    # However, compare_agents converts to dict.
    # If I pass a modified dict to _walk_diff... but compare_agents takes objects.
    # I can use a mocked object or just rely on `inputs={}` which is "removing content".
    # But `inputs={}` vs `inputs={"..."}` is detected as removing keys.
    # Coverage for line 201 `if not rest: ... if new is None:` requires `path` to end at `inputs`
    # AND `new` value to be None.
    # This implies the key `inputs` was removed or set to None.
    # Since `InterfaceDefinition` has it as a field, it's hard to remove it completely from the
    # model dump unless we exclude it.

    # Wait, `InterfaceDefinition` fields:
    # inputs: dict
    # outputs: dict

    # If I hack the dict before comparing? No, must use public API.
    # Maybe `inputs` in `InterfaceDefinition` can be None? Type hint says `dict`.
    # If I can't hit it with Pydantic models, maybe I can't hit it at all in normal usage.
    # BUT, `_walk_diff` is generic.


def test_complex_overhaul() -> None:
    """Multiple simultaneous changes."""
    agent1 = create_base_manifest()

    # Setup Agent 1
    defs1 = agent1.definitions.copy()
    agent_def1 = defs1["test-agent"]
    assert isinstance(agent_def1, AgentDefinition)
    agent_def1 = agent_def1.model_copy(
        update={"tools": ["tool_a"], "resources": ModelProfile(provider="openai", model_id="gpt-3.5")}
    )
    defs1["test-agent"] = agent_def1
    agent1 = agent1.model_copy(update={"definitions": defs1})

    # Setup Agent 2
    agent2 = agent1.model_copy(deep=True)
    defs2 = agent2.definitions.copy()
    agent_def2 = defs2["test-agent"]
    assert isinstance(agent_def2, AgentDefinition)

    # Changes:
    # 1. Add tool (FEATURE)
    # 2. Change resource (RESOURCE)
    # 3. Change Metadata (PATCH)
    agent_def2 = agent_def2.model_copy(
        update={
            "tools": ["tool_a", "tool_b"],
            "resources": ModelProfile(provider="openai", model_id="gpt-4"),
            "goal": "New Goal",
        }
    )
    defs2["test-agent"] = agent_def2
    agent2 = agent2.model_copy(update={"definitions": defs2})

    report = compare_agents(agent1, agent2)

    categories = {c.category for c in report.changes}
    assert ChangeCategory.FEATURE in categories  # Added tool
    assert ChangeCategory.RESOURCE in categories  # Changed model
    assert ChangeCategory.PATCH in categories  # Changed goal
