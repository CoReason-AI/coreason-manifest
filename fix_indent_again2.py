import re

with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    c = f.read()

# Replace the rogue `sort_adapters` before `BaseTopology`
c = c.replace(
    """]


    @model_validator(mode="after")
    def sort_adapters(self) -> Self:
        object.__setattr__(self, "peft_adapters", sorted(self.peft_adapters, key=lambda x: x.adapter_id))
        return self

class BaseTopology(CoreasonBaseModel):""",
    """]

class BaseTopology(CoreasonBaseModel):""",
)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(c)
