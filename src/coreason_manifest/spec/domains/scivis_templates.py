from typing import Annotated

from pydantic import BaseModel, Field

from coreason_manifest.spec.domains.scivis_style import ColorToken

TemplateURN = Annotated[str, Field(pattern=r"^urn:sci-design:[a-z0-9-]+:[a-z0-9-]+:v[0-9]+$")]


class TemplateOverride(BaseModel):
    target_internal_id: str = Field(
        ..., description="The ID of the node *inside* the predefined template being mutated."
    )
    new_label: str | None = None
    new_color_token: ColorToken | None = None
    is_hidden: bool = Field(
        default=False, description="If true, the execution engine will omit this node from the template."
    )


class ComponentTemplate(BaseModel):
    urn: TemplateURN
    overrides: list[TemplateOverride] = Field(default_factory=list)
