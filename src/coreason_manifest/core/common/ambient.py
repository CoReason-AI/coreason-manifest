from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class AmbientTriggerRule(CoreasonModel):
    trigger_events: list[str] = Field(
        ...,
        description="List of headless tool names to listen for (e.g., ['CANVAS_ADD_CONNECTION']).",
    )
    debounce_ms: int = Field(default=800, description="Wait for state to settle before firing.")
    extract_triplets: bool = Field(
        default=True,
        description="If True, the client extracts geometric relationships into Semantic Triplets before firing.",
    )

    @model_validator(mode="after")
    def validate_debounce_ms(self) -> "AmbientTriggerRule":
        if self.debounce_ms < 100 or self.debounce_ms > 5000:
            raise ValueError("debounce_ms must be mathematically sane (>= 100 and <= 5000).")
        return self


class AmbientListenerConfig(CoreasonModel):
    listener_id: str
    target_canvas_id: str = Field(..., description="The ID of the specific MCP UI widget to monitor.")
    trigger_rules: list[AmbientTriggerRule]
    action_route: str = Field(
        ...,
        description="The LangGraph node or agent ID to asynchronously dispatch the extracted intent to.",
    )
    ui_target_pointer: str = Field(
        ...,
        description="The local state pointer where the search results should stream into.",
    )

    @model_validator(mode="after")
    def validate_ui_target_pointer(self) -> "AmbientListenerConfig":
        if not self.ui_target_pointer.startswith("$local."):
            raise ValueError("ui_target_pointer strictly must start with '$local.'")
        return self
