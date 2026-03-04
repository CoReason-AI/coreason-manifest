import pytest
from pydantic import ValidationError

from coreason_manifest.adapters.mcp.clinical import (
    CohortDiagnosticsRequest,
    EpistemicPromptManifest,
    OMOPDomain,
    OMOPResourceTemplate,
)


def test_omop_resource_template_valid() -> None:
    template = OMOPResourceTemplate(
        uri_template="omop://vocab/concept/{concept_id}",
        resource_type=OMOPDomain.CONCEPT,
        description="A concept resource.",
    )
    assert template.uri_template == "omop://vocab/concept/{concept_id}"
    assert template.resource_type == OMOPDomain.CONCEPT


def test_omop_resource_template_invalid_uri() -> None:
    with pytest.raises(ValidationError) as exc_info:
        OMOPResourceTemplate(
            uri_template="http://vocab/concept/{concept_id}",
            resource_type=OMOPDomain.CONCEPT,
            description="Invalid URI protocol.",
        )
    assert "uri_template must follow the 'omop://' protocol pattern" in str(exc_info.value)


def test_cohort_diagnostics_request_valid() -> None:
    request = CohortDiagnosticsRequest(
        inclusion_rules=["rule1", {"type": "json_logic"}],
        target_cohort_ids=[1, 2],
        comparator_cohort_ids=[3],
        evaluation_windows=[0, 30, 365],
        diagnostic_flags={"runInclusionStatistics": True},
    )
    assert request.target_cohort_ids == [1, 2]
    assert request.comparator_cohort_ids == [3]


def test_epistemic_prompt_manifest_valid() -> None:
    manifest = EpistemicPromptManifest(
        prompt_id="test_prompt",
        version="1.0.0",
        instruction_template="You are a helpful assistant.",
        required_guideline_citations=True,
        expected_output_schema="TestSchema",
        reproducibility_hash="hash123",
    )
    assert manifest.prompt_id == "test_prompt"
    assert manifest.required_guideline_citations is True
