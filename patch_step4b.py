with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()


# Remove the validate_grounding_density_for_visuals as compression_sla no longer exists
old_validator = """    @model_validator(mode="after")
    def validate_grounding_density_for_visuals(self) -> Self:
        if (
            "tabular_grid" in self.target_modalities or "raster_image" in self.target_modalities
        ) and self.compression_sla.required_grounding_density == "sparse":
            raise ValueError(
                "Epistemic safety violation: Visual or tabular modalities require strict spatial tracking. 'required_grounding_density' cannot be 'sparse'."
            )
        return self"""

content = content.replace(old_validator, "")

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
