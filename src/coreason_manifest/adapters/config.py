# src/coreason_manifest/spec/interop/adapter_config.py

import os

from pydantic import Field

from coreason_manifest.core.common_base import CoreasonModel


class AdapterConfig(CoreasonModel):
    default_openai_model: str = Field(
        default_factory=lambda: os.environ.get("COREASON_DEFAULT_OPENAI_MODEL", "gpt-4o"),
        description="Default OpenAI model to use when not specified in the node profile.",
    )

    # Can be extended for other providers

    @property
    def fallback_model(self) -> str:
        """Return the default fallback model."""
        return self.default_openai_model
