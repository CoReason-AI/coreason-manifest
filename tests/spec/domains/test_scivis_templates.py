import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.domains.scivis_style import ColorToken
from coreason_manifest.spec.domains.scivis_templates import ComponentTemplate, TemplateOverride


def test_template_urn_valid() -> None:
    # Testing that valid URN strings create ComponentTemplate correctly
    template = ComponentTemplate(urn="urn:sci-design:ml:transformer-block:v1", overrides=[])
    assert template.urn == "urn:sci-design:ml:transformer-block:v1"

    template = ComponentTemplate(urn="urn:sci-design:a-b:c-d:v999", overrides=[])
    assert template.urn == "urn:sci-design:a-b:c-d:v999"


def test_template_urn_invalid() -> None:
    # Testing that invalid strings raise ValidationError
    invalid_urns = [
        "urn:sci-design:ML:transformer-block:v1",  # uppercase not allowed
        "my_template_1",  # completely wrong format
        "urn:sci-design:ml:transformer_block:v1",  # underscore not allowed
        "urn:sci-design:ml:transformer-block:v",  # missing version number
        "urn:other-design:ml:transformer-block:v1",  # wrong prefix
    ]

    for urn in invalid_urns:
        with pytest.raises(ValidationError):
            ComponentTemplate(urn=urn, overrides=[])


@st.composite
def template_override_strategy(draw: st.DrawFn) -> TemplateOverride:
    return TemplateOverride(
        target_internal_id=draw(st.text(min_size=1)),
        new_label=draw(st.one_of(st.none(), st.text())),
        new_color_token=draw(st.one_of(st.none(), st.sampled_from(list(ColorToken)))),
        is_hidden=draw(st.booleans()),
    )


@st.composite
def component_template_strategy(draw: st.DrawFn) -> ComponentTemplate:
    # Use simpler, smaller strings for faster generation
    a = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=10))
    b = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=10))
    c = draw(st.integers(min_value=0, max_value=999))
    urn = f"urn:sci-design:{a}:{b}:v{c}"
    overrides = draw(st.lists(template_override_strategy(), max_size=2))
    return ComponentTemplate(urn=urn, overrides=overrides)


@given(component_template_strategy())
def test_component_template_fuzz(template: ComponentTemplate) -> None:
    assert isinstance(template, ComponentTemplate)
    assert template.urn.startswith("urn:sci-design:")
