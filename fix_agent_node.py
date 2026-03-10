with open("src/coreason_manifest/spec/ontology.py") as f:
    c = f.read()

target = """    anchoring_policy: AnchoringPolicy | None = Field(
        default=None,
        description="The declarative contract mathematically binding this agent to a core altruistic objective.",
    )"""

replacement = """    anchoring_policy: AnchoringPolicy | None = Field(
        default=None,
        description="The declarative contract mathematically binding this agent to a core altruistic objective.",
    )

    @model_validator(mode="after")
    def sort_adapters(self) -> Self:
        object.__setattr__(self, "peft_adapters", sorted(self.peft_adapters, key=lambda x: x.adapter_id))
        return self"""

c = c.replace(target, replacement)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
