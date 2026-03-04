from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.presentation.scivis import MacroGrid


class BaseIntent(CoreasonBaseModel):
    """Base class for presentation intents."""


class DraftingIntent(BaseIntent):
    """Intent indicating the AI is proposing a draft."""

    type: Literal["drafting"] = Field(default="drafting", description="Discriminator for a drafting intent.")


class AdjudicationIntent(BaseIntent):
    """Intent indicating the presentation requires human approval/rejection."""

    type: Literal["adjudication"] = Field(
        default="adjudication",
        description="Discriminator for an adjudication intent.",
    )


class FYIIntent(BaseIntent):
    """Intent indicating the presentation is informational only."""

    type: Literal["fyi"] = Field(default="fyi", description="Discriminator for an FYI intent.")


type AnyIntent = Annotated[DraftingIntent | AdjudicationIntent | FYIIntent, Field(discriminator="type")]


class PresentationEnvelope(CoreasonBaseModel):
    """An envelope wrapping a grid presentation and its intent."""

    intent: AnyIntent = Field(description="The reason an agent is presenting this data to a human.")
    grid: MacroGrid = Field(description="The grid of panels being presented.")
