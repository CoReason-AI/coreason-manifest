import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    c = f.read()

# Fix the stray method at the end of AnyNode type definition (line 3764 approx)
c = c.replace("""    Field(discriminator="type", description="A discriminated union of all valid workflow nodes."),
]


    @model_validator(mode="after")
    def sort_adapters(self) -> Self:
        object.__setattr__(self, "peft_adapters", sorted(self.peft_adapters, key=lambda x: x.adapter_id))
        return self

class BaseTopology(CoreasonBaseModel):""", """    Field(discriminator="type", description="A discriminated union of all valid workflow nodes."),
]

class BaseTopology(CoreasonBaseModel):""")

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(c)
