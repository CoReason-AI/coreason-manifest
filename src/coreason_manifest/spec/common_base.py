from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CommonBase(BaseModel):
    """
    Base model for all Coreason Manifest entities.
    Implements the "Semantic Preservation Funnel" pattern.
    """

    model_config = ConfigDict(extra="allow", strict=True)

    annotations: dict[str, Any] = Field(
        default_factory=dict,
        description="Container for all unrecognized/extension fields (x-extensions).",
    )

    @model_validator(mode="after")
    def funnel_extensions(self) -> "CommonBase":
        """
        Moves all extra fields into the 'annotations' dictionary.
        This ensures strict typing while preserving unknown data for forward compatibility.
        """
        # Pydantic v2 stores extra fields in self.__pydantic_extra__ if extra='allow'
        if self.__pydantic_extra__:
            # Move all extra fields to annotations
            for key, value in self.__pydantic_extra__.items():
                self.annotations[key] = value

            # Clear the extra fields from the model's root namespace to avoid pollution
            # Note: Modifying __pydantic_extra__ directly is the way to remove them from the model dump
            self.__pydantic_extra__.clear()

        return self
