from typing import Any

from coreason_manifest.adapters.config import AdapterConfig
from coreason_manifest.core.compliance import RemediationAction
from coreason_manifest.core.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.state.tools import ToolPack
from coreason_manifest.core.workflow.nodes import AgentNode


def node_to_openai_assistant(node: AgentNode, tool_packs: list[ToolPack] | None = None) -> dict[str, Any]:
    """
    Convert an AgentNode into an OpenAI Assistant definition.

    Args:
        node: The AgentNode to convert.
        tool_packs: A list of available ToolPacks.

    Returns:
        A dictionary representing the OpenAI Assistant configuration.
    """
    if tool_packs is None:
        tool_packs = []

    # Architectural Change: Decouple hardcoded model assumption.
    # Use AdapterConfig to resolve default model from environment or fallback.
    config = AdapterConfig()
    model: str = config.default_openai_model

    if isinstance(node.profile, str):
        # Upgrade: Replace NotImplementedError with SemanticFault ManifestError
        # This guides the user to define the profile inline or implement resolution.
        raise ManifestError.critical_halt(
            code=ManifestErrorCode.CRSN_VAL_INTEGRITY_PROFILE_MISSING,
            message=f"Profile resolution from string ID '{node.profile}' is not yet supported in this adapter version.",
            context={
                "node_id": node.id,
                "remediation": RemediationAction(
                    type="update_field",
                    target_node_id=node.id,
                    description="Expand the profile definition inline instead of using a reference ID.",
                    patch_data=[
                        {
                            "op": "replace",
                            "path": "/profile",
                            "value": {
                                "role": "Assistant",
                                "persona": "Please define persona here.",
                                "reasoning": {"type": "standard", "model": config.default_openai_model},
                            },
                        }
                    ],
                ).model_dump(),
            },
        )

    if node.profile.reasoning and node.profile.reasoning.model:
        model = node.profile.reasoning.model

    # Instructions: Combine role and persona
    instructions = f"{node.profile.role} {node.profile.persona}"

    # Tools: Generate function definitions for every tool listed in node.tools found in tool_packs
    available_tools: set[str] = set()
    for pack in tool_packs:
        available_tools.update(t.name for t in pack.tools)

    tools_definitions = [
        {"type": "function", "function": {"name": tool_name}}
        for tool_name in node.tools
        if tool_name in available_tools
    ]

    return {"name": node.id, "instructions": instructions, "model": model, "tools": tools_definitions}
