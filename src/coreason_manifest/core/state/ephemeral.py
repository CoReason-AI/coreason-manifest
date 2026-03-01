from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class LocalVariableType(StrEnum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


class LocalVariable(CoreasonModel):
    type: LocalVariableType
    default: Any | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_default_type(self) -> "LocalVariable":
        if self.default is not None:
            if self.type == LocalVariableType.STRING and not isinstance(self.default, str):
                raise ValueError("Default value must be a string for STRING type.")
            if self.type == LocalVariableType.NUMBER and (
                not isinstance(self.default, (int, float)) or isinstance(self.default, bool)
            ):
                raise ValueError("Default value must be an int or float for NUMBER type.")
            if self.type == LocalVariableType.BOOLEAN and not isinstance(self.default, bool):
                raise ValueError("Default value must be a bool for BOOLEAN type.")
            if self.type == LocalVariableType.LIST and not isinstance(self.default, list):
                raise ValueError("Default value must be a list for LIST type.")
            if self.type == LocalVariableType.DICT and not isinstance(self.default, dict):
                raise ValueError("Default value must be a dict for DICT type.")
        return self


class LocalStateManifest(CoreasonModel):
    """
    Groups local variables together for the local state manifest.

    These variables are accessed on the client using pointer syntax (e.g., $local.variable_name)
    and do NOT trigger RFC 6902 state patches on the backend.
    """
    keys: dict[str, LocalVariable] = Field(default_factory=dict)
