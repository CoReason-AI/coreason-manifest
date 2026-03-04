from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.state.events import EpistemicEvent, EventType, LegacyPayload


class BaseProjection(ABC, CoreasonModel):
    """
    Base class for Materialized Views.
    Replays the event stream in causal order and folds it into a single Pydantic state model.
    """

    @classmethod
    @abstractmethod
    def project(cls, events: list[EpistemicEvent]) -> Any:
        """
        Folds the event stream into the projection.
        """
        raise NotImplementedError("Subclasses must implement project.")


class DocumentTextProjection(BaseProjection):
    """
    A concrete example projection that aggregates all parsed text blocks.
    """

    aggregated_text: str = Field(default="", description="The aggregated text from all STRUCTURAL_PARSED events.")
    blocks_processed: int = Field(default=0, description="The number of parsed blocks successfully processed.")

    @classmethod
    def project(cls, events: list[EpistemicEvent]) -> "DocumentTextProjection":
        """
        Replays events and builds the DocumentTextProjection state.
        Only processes STRUCTURAL_PARSED events that have a 'text_block' in their payload.
        """
        aggregated_text = ""
        blocks_processed = 0

        for event in events:
            if event.event_type == EventType.STRUCTURAL_PARSED:
                text_block = None
                if isinstance(event.payload, LegacyPayload):
                    text_block = event.payload.data.get("text_block")
                if text_block is not None:
                    # Append text with a newline separator if needed
                    if aggregated_text:
                        aggregated_text += "\n"
                    aggregated_text += str(text_block)
                    blocks_processed += 1

        return cls(aggregated_text=aggregated_text, blocks_processed=blocks_processed)
