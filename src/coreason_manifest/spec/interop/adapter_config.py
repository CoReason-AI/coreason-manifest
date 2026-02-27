# src/coreason_manifest/spec/interop/adapter_config.py

import os
from typing import Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel

class AdapterConfig(CoreasonModel):
    """
    Configuration for LLM adapters.
    Resolves defaults from environment variables to decouple hardcoded assumptions.
    """

    default_openai_model: str = Field(
        default_factory=lambda: os.environ.get("COREASON_DEFAULT_OPENAI_MODEL", "gpt-4o"),
        description="Default OpenAI model to use when not specified in the node profile."
    )

    # Can be extended for other providers

    @property
    def fallback_model(self) -> str:
        return self.default_openai_model

# Singleton instance or factory could be used, but Pydantic models are usually instantiated when needed.
# However, for global defaults, we might want a shared instance or just use the class defaults.
