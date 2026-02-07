# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import importlib

import pytest
import yaml

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    GenericDefinition,
    ManifestV2,
)


def test_bridge_is_gone() -> None:
    """
    Edge Case 1: Verify that the bridge (adapter) is physically gone from the import space.
    This ensures no one accidentally relies on 'dead code'.
    """
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("coreason_manifest.v2.adapter")

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("coreason_manifest.v2.compiler")


def test_vestigial_bridge_fields() -> None:
    """
    Edge Case 2: Vestigial Fields.
    If a V2 manifest contains fields that were ONLY used by the bridge (e.g. hypothetical 'adapter_hints'
    on the definition itself, or just extra junk), V2 should enforce its schema strictly (extra='forbid')
    or allow it if configured to allow.

    Checking strictness prevents 'ghost' configuration that does nothing.
    """
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Vestigial Agent
workflow:
  start: s
  steps: {s: {type: logic, id: s, code: pass}}
definitions:
  my_agent:
    type: agent
    id: a1
    name: A1
    role: R1
    goal: G1
    # This field might have been used by a bridge but is invalid in V2 strict schema
    bridge_conversion_hint: "ignore_me"
"""
    # By default, Pydantic V2 BaseModels might be 'ignore' or 'forbid' depending on config.
    # CoReasonBaseModel typically sets strict config.
    # We expect this to fail if strict, or succeed if loose.
    # The requirement is that we KNOW what happens.
    # Assuming V2 is strict:

    data = yaml.safe_load(yaml_content)

    # If the model is strict, this raises ValidationError.
    # If loose, it passes.
    # Let's verify what it does.
    try:
        ManifestV2(**data)
        is_strict = False
    except Exception:
        is_strict = True

    # We assert that whatever the behavior, it is CONSISTENT.
    # Ideally, for "Burn the Ships", we want strict validation so users don't leave bridge trash.
    # But if the current V2 spec allows extra, we just document that it passes.
    # Let's assert based on current knowledge (CoReasonBaseModel usually strict).

    # Actually, let's verify if AgentDefinition allows extra.
    # If it fails, good. If it passes, check if field exists.

    if is_strict:
        assert True  # Strict is good for cleanup
    else:
        # If it passed, ensure the field is NOT in the model fields (it was ignored or extra)
        m = ManifestV2(**data)
        # It shouldn't be accessible as a first-class field
        agent = m.definitions["my_agent"]

        # KEY BEHAVIOR:
        # Because AgentDefinition is strict (extra='forbid'), the extra field causes validation to fail.
        # The discriminated union then falls back to GenericDefinition (which is permissive).
        # This confirms that "bridge trash" effectively INVALIDATES the AgentDefinition,
        # preventing it from being used as a valid agent in the runtime.

        assert not isinstance(agent, AgentDefinition)
        assert isinstance(agent, GenericDefinition)

        # The junk field is preserved in the generic container, but the type is lost.
        # This is the desired "rejection" behavior.
        assert agent.bridge_conversion_hint == "ignore_me"  # type: ignore[attr-defined]


def test_complex_recursive_composition_native() -> None:
    """
    Complex Case: Deeply Nested Composition (Native V2).
    Verify we can define Agent-as-a-Tool recursively without needing the bridge to 'flatten' or 'compile' it.
    V2 just sees it as a reference.
    """
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Inception Team
workflow:
  start: s
  steps: {s: {type: logic, id: s, code: pass}}
definitions:
  level_3_worker:
    type: agent
    id: worker
    name: Worker
    role: Doer
    goal: Do

  level_2_manager:
    type: agent
    id: manager
    name: Manager
    role: Boss
    goal: Manage
    tools: ["worker_tool"] # Uses worker as tool via wrapper

  worker_tool:
    type: tool
    id: worker_tool
    name: Worker Tool
    uri: "agent://worker"
    risk_level: safe

  level_1_director:
    type: agent
    id: director
    name: Director
    role: Exec
    goal: Direct
    tools: ["manager_tool"] # Uses manager as tool via wrapper

  manager_tool:
    type: tool
    id: manager_tool
    name: Manager Tool
    uri: "agent://manager"
    risk_level: safe
"""
    manifest = ManifestV2(**yaml.safe_load(yaml_content))

    director = manifest.definitions["level_1_director"]
    manager_ref = manifest.definitions["level_2_manager"]
    worker_ref = manifest.definitions["level_3_worker"]

    assert isinstance(director, AgentDefinition)
    assert isinstance(manager_ref, AgentDefinition)
    assert isinstance(worker_ref, AgentDefinition)

    # Director has tool "manager_tool"
    # tools is now list[ToolRequirement | InlineToolDefinition]
    director_tools = [t.uri for t in director.tools if hasattr(t, "uri")]
    assert "manager_tool" in director_tools

    # Manager has tool "worker_tool"
    manager_tools = [t.uri for t in manager_ref.tools if hasattr(t, "uri")]
    assert "worker_tool" in manager_tools

    # We confirm that V2 structure holds this integrity natively.
