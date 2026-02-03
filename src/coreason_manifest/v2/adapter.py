# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Adapter module for backward compatibility with V1 Runtime."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from coreason_manifest.common import ToolRiskLevel
from coreason_manifest.definitions.agent import (
    AgentCapability,
    AgentDependencies,
    AgentMetadata,
    AgentRuntimeConfig,
    AgentStatus,
    CapabilityType,
    DeliveryMode,
    ModelConfig,
    Persona,
    ToolRequirement,
)
from coreason_manifest.definitions.agent import (
    AgentDefinition as V1AgentDefinition,
)
from coreason_manifest.definitions.topology import StateDefinition
from coreason_manifest.recipes import PolicyConfig, RecipeInterface, RecipeManifest
from coreason_manifest.v2.compiler import compile_to_topology
from coreason_manifest.v2.spec.definitions import AgentDefinition as V2AgentDefinition
from coreason_manifest.v2.spec.definitions import ManifestV2, ToolDefinition


def _convert_tool_ref(tool_ref: str, definitions: Dict[str, Any]) -> ToolRequirement:
    """Convert a tool reference (ID) to a V1 ToolRequirement.

    Args:
        tool_ref: The ID of the tool in the V2 definitions.
        definitions: The definitions dictionary from the manifest.

    Returns:
        A V1 ToolRequirement.
    """
    tool_def = definitions.get(tool_ref)

    # Defaults
    uri = f"mcp://{tool_ref}"
    risk_level = ToolRiskLevel.STANDARD

    if isinstance(tool_def, ToolDefinition):
        uri = str(tool_def.uri)
        risk_level = tool_def.risk_level

    # Generate a deterministic hash for the tool requirement (required by V1)
    # In a real system, this should be the actual hash of the tool's source/spec
    tool_hash = hashlib.sha256(uri.encode()).hexdigest()

    return ToolRequirement(
        uri=uri,
        hash=tool_hash,
        scopes=[],  # V2 doesn't have scopes yet
        risk_level=risk_level,
    )


def _convert_agent(agent_v2: V2AgentDefinition, definitions: Dict[str, Any]) -> V1AgentDefinition:
    """Convert a V2 AgentDefinition to a V1 AgentDefinition.

    Args:
        agent_v2: The V2 agent definition.
        definitions: The definitions dictionary from the manifest (for resolving tools).

    Returns:
        The converted V1 AgentDefinition.
    """
    # Ensure ID is a UUID
    try:
        agent_id = UUID(agent_v2.id)
    except ValueError:
        agent_id = uuid5(NAMESPACE_DNS, agent_v2.id)

    # Convert Tools
    tools = []
    for tool_ref in agent_v2.tools:
        tools.append(_convert_tool_ref(tool_ref, definitions))

    # Construct Metadata
    metadata = AgentMetadata(
        id=agent_id,
        version="0.1.0",
        name=agent_v2.name,
        author="system",
        created_at=datetime.now(timezone.utc),
        requires_auth=False,
    )

    # Construct Capability (Default Chat)
    capabilities = [
        AgentCapability(
            name="chat",
            type=CapabilityType.ATOMIC,
            description="Default chat capability",
            inputs={"type": "object", "properties": {"message": {"type": "string"}}},
            outputs={"type": "object", "properties": {"response": {"type": "string"}}},
            delivery_mode=DeliveryMode.REQUEST_RESPONSE,
        )
    ]

    # Construct Config
    persona = Persona(
        name=agent_v2.role, description=agent_v2.goal, directives=[agent_v2.backstory] if agent_v2.backstory else []
    )

    model_config = ModelConfig(
        model=agent_v2.model or "gpt-4", temperature=0.7, system_prompt=agent_v2.backstory, persona=persona
    )

    # V1 requires atomic agents to have system_prompt in config OR llm_config
    runtime_config = AgentRuntimeConfig(llm_config=model_config, system_prompt=agent_v2.backstory)

    dependencies = AgentDependencies(tools=tools, libraries=())

    return V1AgentDefinition(
        metadata=metadata,
        capabilities=capabilities,
        config=runtime_config,
        dependencies=dependencies,
        status=AgentStatus.DRAFT,
    )


def v2_to_recipe(manifest: ManifestV2) -> RecipeManifest:
    """Convert a V2 Manifest into a V1 RecipeManifest.

    Args:
        manifest: The V2 manifest to convert.

    Returns:
        The converted RecipeManifest compatible with the V1 engine.
    """
    # Generate a random ID as V2 manifests don't strictly require one at the root
    # In a real system, this might be consistent or derived from name/version
    recipe_id = str(uuid4())

    # Compile the topology
    topology = compile_to_topology(manifest)

    # Convert metadata
    # We dump to dict to handle potential Pydantic model vs dict
    design_metadata = {}
    if manifest.metadata.design_metadata:
        design_metadata = manifest.metadata.design_metadata.model_dump(by_alias=True, exclude_none=True)

    # Determine persistence
    backend = (manifest.state.backend or "ephemeral").lower()
    # If explicitly not ephemeral/memory, treat as persistent (e.g., redis, sql)
    persistence = "persistent" if backend not in ("ephemeral", "memory") else "ephemeral"

    # Process parameters/definitions
    # We create a new dict to store processed definitions
    parameters: Dict[str, Any] = {}
    for key, value in manifest.definitions.items():
        if isinstance(value, V2AgentDefinition):
            # Convert V2 Agent to V1 Agent
            parameters[key] = _convert_agent(value, manifest.definitions)
        else:
            # Keep as is (ToolDefinition or Any)
            parameters[key] = value

    # Construct the RecipeManifest
    return RecipeManifest(
        id=recipe_id,
        version="0.1.0",  # Default version
        name=manifest.metadata.name,
        description=None,
        interface=RecipeInterface(inputs=manifest.interface.inputs, outputs=manifest.interface.outputs),
        state=StateDefinition(schema_=manifest.state.schema_, persistence=persistence),
        policy=PolicyConfig(
            max_steps=manifest.policy.max_steps,
            max_retries=manifest.policy.max_retries,
            timeout=manifest.policy.timeout,
            human_in_the_loop=manifest.policy.human_in_the_loop,
        ),
        parameters=parameters,
        topology=topology,
        metadata=design_metadata,
    )
