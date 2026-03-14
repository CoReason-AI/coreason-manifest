# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from pydantic import Field, model_validator

from coreason_manifest.spec.ontology import CoreasonBaseState, LineageWatermarkReceipt


class Assertion(CoreasonBaseState):
    """
    A structural claim bound to the C2PA manifest.
    """
    label: str = Field(description="The unique label for the assertion (e.g., c2pa.actions).")
    data: dict[str, Any] = Field(description="The structured data backing the claim.")

    @model_validator(mode="after")
    def _enforce_data_bounds(self) -> "Assertion":
        from coreason_manifest.spec.ontology import _validate_payload_bounds
        object.__setattr__(self, "data", _validate_payload_bounds(self.data))
        return self


class ClaimSignature(CoreasonBaseState):
    """
    Cryptographic signature mathematically securing the C2PA claim.
    """
    issuer: str = Field(description="The verified DID of the issuer.")
    signature_data: str = Field(description="Base64 encoded cryptographic signature payload.")


class Ingredient(CoreasonBaseState):
    """
    A strictly typed assertion referencing the origin or components used to build the asset.
    Translates structurally from a LineageWatermarkReceipt.
    """
    title: str = Field(description="The human-readable title of the ingredient.")
    document_id: str = Field(description="The unique reference identifier.")
    provenance_watermark: LineageWatermarkReceipt | None = Field(
        default=None,
        description="The internal swarm watermarking receipt mathematically bound as a C2PA ingredient."
    )


class C2PAManifest(CoreasonBaseState):
    """
    The structural C2PA schema mapping the swarm's internal EpistemicProvenanceReceipt
    DAGs into a mathematically valid, externally verifiable manifest.
    """
    claim_generator: str = Field(
        description="The deterministic identifier of the generative orchestrator that composed the manifest."
    )
    assertions: list[Assertion] = Field(
        description="The structural claims included in this manifest."
    )
    ingredients: list[Ingredient] = Field(
        description="The passive structural mapping showing origin provenance."
    )
    signature: ClaimSignature = Field(
        description="The cryptographic validation mathematically sealing the C2PA payload."
    )

    @model_validator(mode="after")
    def _sort_arrays(self) -> "C2PAManifest":
        object.__setattr__(self, "assertions", sorted(self.assertions, key=lambda x: x.label))
        object.__setattr__(self, "ingredients", sorted(self.ingredients, key=lambda x: x.document_id))
        return self
