from typing import Any, Protocol

from coreason_manifest.core.state import ToolPack
from coreason_manifest.core.workflow import AgentNode


class GenerativeAdapter(Protocol):
    """
    Protocol defining the contract for Large Language Model (LLM) providers.
    All external generative models (OpenAI, Anthropic, etc.) must implement this interface.
    """

    def node_to_provider_assistant(self, node: AgentNode, tool_packs: list[ToolPack] | None = None) -> dict[str, Any]:
        """
        Converts an AgentNode definition into a provider-specific assistant payload.

        Args:
            node: The AgentNode to convert.
            tool_packs: A list of available ToolPacks.

        Returns:
            A dictionary representing the provider-specific assistant configuration.
        """
        ...
