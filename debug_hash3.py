from pydantic import BaseModel, model_validator, ConfigDict
from typing import Any

class T(BaseModel):
    model_config = ConfigDict(frozen=True)
    items: list[str]

    def model_post_init(self, __context: Any) -> None:
        print("model_post_init called. items:", self.items)

    @model_validator(mode="after")
    def sort_items(self) -> Any:
        print("model_validator called. items:", self.items)
        object.__setattr__(self, "items", sorted(self.items))
        return self

t = T(items=["b", "a"])
