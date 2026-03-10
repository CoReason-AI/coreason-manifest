# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AnyPanel,
    DynamicLayoutManifest,
    GrammarPanel,
    InsightCard,
    MacroGridProfile,
    VisualEncodingProfile,
)


@pytest.mark.parametrize(
    "payload",
    [
        "getattr(__builtins__, 'ev' + 'al')('print(\\'hacked\\')')",
        "__import__('o' + 's').system('echo 1')",
        "__import__('subprocess').run(['echo', '1'])",
    ],
)
def test_dynamic_layout_template_rejects_obfuscated_rce(payload: str) -> None:
    """
    AGENT INSTRUCTION: Verify the AST boundary deterministically severs
    polymorphic string concatenation attacks prior to instantiation.
    """
    with pytest.raises(ValidationError, match="Kinetic execution bleed detected"):
        DynamicLayoutManifest(layout_tstring=payload)


@pytest.mark.parametrize(
    "payload",
    [
        "Not a python string at all",
        't"{user_name}"',
        "{{ safe_variable }}",
    ],
)
def test_dynamic_layout_template_allows_valid_strings(payload: str) -> None:
    """
    Verify that strings not containing function calls, or strings that
    are syntactically invalid Python, are allowed to pass the AST boundary.
    """
    template = DynamicLayoutManifest(layout_tstring=payload)
    assert template.layout_tstring == payload


@given(
    payload=st.sampled_from(
        [
            "t\"{__import__('os').system('rm -rf /')}\"",
            "t\"{eval('1+1')}\"",
            "t\"{open('/etc/shadow').read()}\"",
            "t\"{exec('import sys')}\"",
        ]
    )
)
def test_tstring_rce_fuzzer(payload: str) -> None:
    """
    1. The T-String RCE Fuzzer:
    Generate adversarial payload strings and prove that DynamicLayoutManifest
    definitively raises a ValidationError when instantiated with them.
    """
    with pytest.raises(ValidationError, match="Kinetic execution bleed detected"):
        DynamicLayoutManifest(layout_tstring=payload)


@given(
    payload=st.sampled_from(
        [
            "<script>alert(1)</script>",
            '<a href="javascript:void(0)">',
            '<iframe src="malicious.com">',
            "<SCRIPT>alert(1)</SCRIPT>",
            "<object data='data:text/html;base64,...'></object>",
            "<embed src='malicious.swf'>",
        ]
    )
)
def test_polymorphic_xss_proof(payload: str) -> None:
    """
    2. The Polymorphic XSS Proof:
    Generate adversarial Markdown strings containing malicious tags
    and prove that InsightCard definitively rejects them via a ValidationError.
    """
    with pytest.raises(ValidationError, match="HTML tags are prohibited"):
        InsightCard(panel_id="panel_1", title="Insight Title", markdown_content=payload)


@given(
    payload=st.sampled_from(
        [
            "<img src='x' onerror='alert(1)'>",
            "<svg onload=alert(1)>",
            '<body onmouseover="javascript:alert(1)">',
        ]
    )
)
def test_polymorphic_event_handler_proof(payload: str) -> None:
    """
    2.1 The Polymorphic Event Handler Proof:
    Generate adversarial strings with inline HTML event handlers and prove they are rejected.
    """
    with pytest.raises(ValidationError, match="Forbidden HTML event handler detected"):
        InsightCard(panel_id="panel_1", title="Insight Title", markdown_content=payload)


@given(
    ghost_id=st.text(min_size=1).filter(lambda x: x != "panel_1" and x != "panel_2"),
)
def test_visual_ghost_node_test(ghost_id: str) -> None:
    """
    3. The Visual Ghost Node Test (Adversarial):
    Generate a MacroGridProfile payload where the layout_matrix contains a string ID
    that is absent from the panels list. Prove the model_validator catches this
    and raises a ValidationError.
    """
    panels: list[AnyPanel] = [
        InsightCard(panel_id="panel_1", title="A", markdown_content="Safe text"),
        GrammarPanel(panel_id="panel_2", title="B", data_source_id="d1", mark="point", encodings=[]),
    ]

    escaped_ghost_id = re.escape(ghost_id)
    with pytest.raises(ValidationError, match=f"Ghost Panel referenced in layout_matrix: {escaped_ghost_id}"):
        MacroGridProfile(layout_matrix=[["panel_1", "panel_2"], [ghost_id, "panel_1"]], panels=panels)


@given(
    title=st.text(min_size=1),
    safe_text=st.text().filter(
        lambda x: not bool(re.search(r"<[^=\s\d]", x)) and not bool(re.search(r"on[a-zA-Z]+\s*=", x.lower()))
    ),
    x_label=st.text(min_size=1),
    y_label=st.text(min_size=1),
)
def test_safe_rendering_test(title: str, safe_text: str, x_label: str, y_label: str) -> None:
    """
    4. The Safe Rendering Test (Success):
    Generate a structurally perfect MacroGridProfile with a valid layout_matrix
    that perfectly maps to the generated panel_ids, featuring clean text.
    Prove it instantiates successfully.
    """
    panels: list[AnyPanel] = [
        InsightCard(panel_id="panel_1", title=title, markdown_content=safe_text),
        GrammarPanel(
            panel_id="panel_2",
            title=x_label,
            data_source_id="d2",
            mark="point",
            encodings=[VisualEncodingProfile(channel="x", field="x"), VisualEncodingProfile(channel="y", field="y")],
        ),
        GrammarPanel(
            panel_id="panel_3",
            title=y_label,
            data_source_id="d3",
            mark="bar",
            encodings=[
                VisualEncodingProfile(channel="x", field="step"),
                VisualEncodingProfile(channel="y", field="count"),
            ],
        ),
    ]

    # Instantiate without error
    grid = MacroGridProfile(layout_matrix=[["panel_1", "panel_2"], ["panel_3", "panel_1"]], panels=panels)
    assert grid.layout_matrix == [["panel_1", "panel_2"], ["panel_3", "panel_1"]]
    assert len(grid.panels) == 3


@given(scheme=st.sampled_from(["javascript", "vbscript", "data", "JaVaScRiPt"]), payload=st.text())
def test_insight_card_rejects_xss_links(scheme: str, payload: str) -> None:
    # Use 'payload' that does not contain `<` or `on...=` to bypass sanitize_markdown
    payload = payload.replace("<", "").replace("on", "")
    malicious_markdown = f"Look at this: [click me]({scheme}:{payload})"
    with pytest.raises(ValidationError, match="Malicious executable link scheme detected"):
        InsightCard(panel_id="test_xss", title="XSS Test", markdown_content=malicious_markdown)
