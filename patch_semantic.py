with open("src/coreason_manifest/state/semantic.py", "r") as f:
    content = f.read()

import_target = "from pydantic import Field"
import_replacement = "from pydantic import Field, model_validator\nfrom typing import Any"
if "model_validator" not in content:
    content = content.replace(import_target, import_replacement)

target = """class TemporalBounds(CoreasonBaseModel):
    valid_from: float | None = Field(default=None, description="The UNIX timestamp when this memory became true.")
    valid_to: float | None = Field(default=None, description="The UNIX timestamp when this memory was invalidated.")
    interval_type: CausalInterval | None = Field(
        default=None, description="The Allen's interval algebra or causal relationship classification."
    )"""

replacement = target + """

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Any:
        if self.valid_from is not None and self.valid_to is not None:
            if self.valid_to < self.valid_from:
                raise ValueError("valid_to cannot be before valid_from")
        return self"""

content = content.replace(target, replacement)

with open("src/coreason_manifest/state/semantic.py", "w") as f:
    f.write(content)
