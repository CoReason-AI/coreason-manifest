with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

# For DifferentiableLogicConstraint
dlc_old = """    @model_validator(mode="after")
    def validate_domain_extensions(self, info: ValidationInfo) -> Self:
        allowed_exts = (info.context or {}).get("allowed_ext_intents", set())
        for k, v in self.__dict__.items():
            if isinstance(v, str) and v.startswith("ext:") and v not in allowed_exts:
                raise ValueError(f"Unauthorized extension string in field {k}: {v}")
            elif isinstance(v, dict):
                for dk, dv in v.items():
                    if isinstance(dk, str) and dk.startswith("ext:") and dk not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict key of {k}: {dk}")
                    if isinstance(dv, str) and dv.startswith("ext:") and dv not in allowed_exts:
                        raise ValueError(f"Unauthorized extension string in dict value of {k}: {dv}")
        return self"""

dlc_new = """    @model_validator(mode="after")
    def validate_domain_extensions(self, info: ValidationInfo) -> Self:
        allowed_exts = (info.context or {}).get("allowed_ext_intents", set())
        for k, v in self.__dict__.items():
            if isinstance(v, str) and v.startswith("ext:") and v not in allowed_exts:
                raise ValueError(f"Unauthorized extension string in field {k}: {v}")
        return self"""

content = content.replace(dlc_old, dlc_new)

# For EpistemicAxiomState (same old code)
content = content.replace(dlc_old, dlc_new)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)

print("Updated DifferentiableLogicConstraint and EpistemicAxiomState validators.")
