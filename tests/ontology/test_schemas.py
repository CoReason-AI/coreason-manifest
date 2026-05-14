# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from pydantic import AnyUrl, TypeAdapter

from coreason_manifest.spec.ontology import (
    EpistemicOntologicalCrosswalkIntent,
    EpistemicSemanticValidationSLA,
    SchemaDrivenExtractionSLA,
)

url_adapter = TypeAdapter(AnyUrl)


def test_ontological_crosswalk_intent_sorting() -> None:
    intent = EpistemicOntologicalCrosswalkIntent(
        target_graph_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        source_strings=["zebra", "apple", "banana"],
        target_ontology_registries=["HP", "CHEBI", "MONDO"],
        minimum_isometry_threshold=0.8,
    )
    assert intent.source_strings == ["apple", "banana", "zebra"]
    assert intent.target_ontology_registries == ["CHEBI", "HP", "MONDO"]


def test_schema_driven_extraction_sla_validation() -> None:
    with pytest.raises(ValueError, match="Epistemic Violation"):
        SchemaDrivenExtractionSLA(
            schema_registry_uri=url_adapter.validate_python("https://example.com/schema"),
            extraction_framework="urn:coreason:extraction:ontogpt_spires",
            max_schema_retries=3,
            validation_failure_action="drop_edge",
            linkml_governance=None,
        )

    # Should pass
    sla = SchemaDrivenExtractionSLA(
        schema_registry_uri=url_adapter.validate_python("https://example.com/schema"),
        extraction_framework="urn:coreason:extraction:ontogpt_spires",
        max_schema_retries=3,
        validation_failure_action="drop_edge",
        linkml_governance=EpistemicSemanticValidationSLA(
            linkml_schema_uri=url_adapter.validate_python("https://example.com/linkml")
        ),
    )
    assert sla.linkml_governance is not None
