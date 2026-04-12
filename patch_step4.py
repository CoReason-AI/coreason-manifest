with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()


# EpistemicTransmutationTask refactoring
target_modalities_old = 'target_modalities: list[\n        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor"]\n    ]'
target_modalities_new = 'target_modalities: list[\n        Literal["text", "raster_image", "vector_graphics", "tabular_grid", "n_dimensional_tensor", "semantic_graph"]\n    ]'
content = content.replace(target_modalities_old, target_modalities_new)

compression_sla_old = '    compression_sla: EpistemicCompressionSLA = Field(\n        description="The strict mathematical boundary defining the maximum allowed informational entropy loss."\n    )'
compression_sla_new = "    schema_governance: SchemaDrivenExtractionSLA | None = Field(default=None)"
content = content.replace(compression_sla_old, compression_sla_new)

# Add validator
validator_code = """
    @model_validator(mode="after")
    def validate_graph_schema_presence(self) -> Self:
        if "semantic_graph" in self.target_modalities and self.schema_governance is None:
            raise ValueError("schema_governance is strictly required when target_modalities includes 'semantic_graph'.")
        return self
"""

# inject validator before "    def _enforce_canonical_sort(self) -> Self:" inside EpistemicTransmutationTask
content = content.replace(
    '    @model_validator(mode="after")\n    def _enforce_canonical_sort(self) -> Self:\n        object.__setattr__(self, "target_modalities", sorted(self.target_modalities))',
    validator_code
    + '\n    @model_validator(mode="after")\n    def _enforce_canonical_sort(self) -> Self:\n        object.__setattr__(self, "target_modalities", sorted(self.target_modalities))',
)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
