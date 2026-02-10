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
    ManifestV2,
    compare_agents,
)
from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.diff import _walk_diff, DiffChange


def create_base_manifest() -> ManifestV2:
    return AgentBuilder("test-agent").build()


def update_agent_tools(manifest: ManifestV2, tools: list) -> ManifestV2:
    defs = manifest.definitions.copy()
    agent_def = defs["test-agent"]
    assert isinstance(agent_def, AgentDefinition)
    new_agent_def = agent_def.model_copy(update={"tools": tools})
    defs["test-agent"] = new_agent_def
    return manifest.model_copy(update={"definitions": defs})


def test_nested_structures() -> None:
    """Cover _make_hashable for nested dicts (line 83) and lists (line 85)."""
    agent1 = create_base_manifest()

    tool_a = {
        "type": "inline",
        "name": "tool_a",
        "description": "desc",
        "parameters": {"type": "object", "properties": {"nested_list": ["a", "b"], "nested_dict": {"k": "v"}}},
    }

    tool_b = {
        "type": "inline",
        "name": "tool_a",
        "description": "desc",
        "parameters": {
            "type": "object",
            "properties": {
                "nested_list": ["a", "c"],  # Changed to prevent early return in _walk_diff
                "nested_dict": {"k": "v"},
            },
        },
    }

    agent1 = update_agent_tools(agent1, [tool_a])
    agent2 = update_agent_tools(create_base_manifest(), [tool_b])

    # This should now force _make_hashable to recurse into nested_list because
    # the top-level tools list items are different.
    report = compare_agents(agent1, agent2)
    assert len(report.changes) > 0


def test_replace_op() -> None:
    """Cover 'replace' opcode logic (lines 137-156)."""
    t1 = {"type": "remote", "uri": "u1"}
    t2 = {"type": "remote", "uri": "u2"}
    t3 = {"type": "remote", "uri": "u3"}
    t4 = {"type": "remote", "uri": "u4"}

    # Case 1: Same length replace (Covered previously, keeping for robustness)
    agent1 = update_agent_tools(create_base_manifest(), [t1, t2, t3])
    agent2 = update_agent_tools(create_base_manifest(), [t1, t4, t3])
    report = compare_agents(agent1, agent2)
    assert any("tools.1.uri" in c.path for c in report.changes)

    # Case 2: Length mismatch (Insertions) - Covered previously
    agent3 = update_agent_tools(create_base_manifest(), [t2])
    agent4 = update_agent_tools(create_base_manifest(), [t3, t4])
    report2 = compare_agents(agent3, agent4)
    assert any("tools.0.uri" in c.path for c in report2.changes)  # Modified
    assert any("tools.1" in c.path and c.old_value is None for c in report2.changes)  # Added

    # Case 3: Length mismatch (Deletions) - Lines 149-151
    # ["a", "b"] -> ["c"]
    # Replace 2 items with 1 item.
    agent5 = update_agent_tools(create_base_manifest(), [t1, t2])
    agent6 = update_agent_tools(create_base_manifest(), [t3])

    report3 = compare_agents(agent5, agent6)
    # t1 vs t3 -> replace/diff
    # t2 -> deleted

    # Check if we hit the deletion block in replace logic
    # This depends on difflib. If it sees replace (0,2) -> (0,1).
    # Then len_old=2, len_new=1. common=1.
    # Loop k=0: t1 vs t3.
    # Loop k=1 to 2: delete t2.

    assert any("tools.0.uri" in c.path for c in report3.changes)  # t1 vs t3
    assert any("tools.1" in c.path and c.new_value is None for c in report3.changes)  # t2 deleted


def test_fallback_exception() -> None:
    """Cover fallback logic by forcing an exception in difflib/hashing (lines 168-179)."""

    changes: list[DiffChange] = []

    # Case 1: Equal lengths (Covered previously)
    _walk_diff("root", [{"val": {1, 2}}], [{"val": {1, 3}}], changes)
    assert len(changes) > 0

    # Case 2: Unequal lengths to cover lines 176-179
    # Old > New (Deletion)
    changes = []
    _walk_diff("del", [{"v": {1}}, {"v": {2}}], [{"v": {1}}], changes)
    # Index 0 match. Index 1 delete.
    assert any(c.path == "del.1" and c.new_value is None for c in changes)

    # New > Old (Insertion)
    changes = []
    _walk_diff("ins", [{"v": {1}}], [{"v": {1}}, {"v": {2}}], changes)
    # Index 0 match. Index 1 insert.
    assert any(c.path == "ins.1" and c.old_value is None for c in changes)
